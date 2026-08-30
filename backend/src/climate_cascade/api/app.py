"""FastAPI control plane for durable runs and reconnectable progress events."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from climate_cascade.domain import RunMode
from climate_cascade.persistence import LocalArtifactStore, RunRepository, RunSnapshot, create_sqlite_engine, migrate_database

from .models import CreateBaselineRunRequest, CreateRunRequest, RunResponse


@dataclass(frozen=True)
class ApiServices:
    repository: RunRepository
    artifact_store: LocalArtifactStore
    case_root: Path


def build_services(*, database_url: str, artifact_root: Path, case_root: Path, repository_root: Path) -> ApiServices:
    migrate_database(database_url, repository_root=repository_root)
    return ApiServices(
        repository=RunRepository(create_sqlite_engine(database_url)),
        artifact_store=LocalArtifactStore(artifact_root),
        case_root=case_root,
    )


def create_app(*, services: ApiServices) -> FastAPI:
    app = FastAPI(title="Climate Cascade Response API", version="0.1.0")

    @app.middleware("http")
    async def correlation_id(request: Request, call_next):
        request.state.correlation_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.correlation_id
        return response

    @app.exception_handler(KeyError)
    async def unknown_run(request: Request, error: KeyError):
        return _error_response(request, 404, "RUN_NOT_FOUND", f"Unknown run: {error.args[0]}")

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        code = "REQUEST_INVALID" if error.status_code < 500 else "INTERNAL_ERROR"
        return _error_response(request, error.status_code, code, str(error.detail))

    @app.get("/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ready"}

    @app.get("/v1/cases")
    def list_cases() -> dict[str, list[dict[str, str]]]:
        cases = []
        for manifest_path in sorted(services.case_root.glob("*/manifest.json")):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            cases.append({"case_id": manifest["fixture_id"], "hazard_type": manifest["hazard_type"]})
        return {"cases": cases}

    @app.post("/v1/runs", response_model=RunResponse, status_code=202)
    def create_run(
        request: Request,
        payload: CreateRunRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> RunResponse:
        return _create_run(request, payload, idempotency_key=idempotency_key, services=services)

    @app.post("/v1/baseline/runs", response_model=RunResponse, status_code=202)
    def create_baseline_run(
        request: Request,
        payload: CreateBaselineRunRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> RunResponse:
        run_request = CreateRunRequest(
            case_id=payload.case_id,
            mode=RunMode.BASELINE,
            fixture_mode=payload.fixture_mode,
            model=payload.model,
            api_key_env=payload.api_key_env,
        )
        return _create_run(request, run_request, idempotency_key=idempotency_key, services=services)

    @app.get("/v1/runs/{run_id}", response_model=RunResponse)
    def get_run(run_id: str) -> RunResponse:
        return _run_response(services.repository.get_run(run_id))

    @app.get("/v1/runs/{run_id}/baseline")
    def get_baseline_artifacts(run_id: str) -> dict[str, object]:
        services.repository.get_run(run_id)
        payload: dict[str, object] = {"run_id": run_id}
        for logical_name in ("baseline_run", "baseline_evaluation"):
            artifact = services.repository.get_artifact(run_id, logical_name)
            if artifact is not None:
                payload[logical_name] = json.loads(artifact.storage_path.read_text(encoding="utf-8"))
        return payload

    @app.get("/v1/runs/{run_id}/events")
    async def stream_events(
        run_id: str,
        after_sequence: int = 0,
        follow: bool = True,
        last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    ) -> StreamingResponse:
        services.repository.get_run(run_id)
        if last_event_id and last_event_id.isdigit():
            after_sequence = max(after_sequence, int(last_event_id))

        async def event_stream():
            sequence = after_sequence
            while True:
                events = services.repository.list_events(run_id, after_sequence=sequence)
                for event in events:
                    sequence = event.sequence
                    data = {
                        "sequence": event.sequence,
                        "event_type": event.event_type,
                        "stage": event.stage.value,
                        "status": event.status,
                        "message": event.message,
                        "evidence_ids": event.evidence_ids,
                        "retry_count": event.retry_count,
                        "created_at": event.created_at.isoformat(),
                    }
                    yield f"id: {event.sequence}\nevent: run_event\ndata: {json.dumps(data, separators=(',', ':'))}\n\n"
                if not follow:
                    return
                await asyncio.sleep(0.25)

        return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})

    return app


def _create_run(
    request: Request, payload: CreateRunRequest, *, idempotency_key: str | None, services: ApiServices
) -> RunResponse:
    if not idempotency_key or len(idempotency_key.strip()) < 8:
        raise HTTPException(status_code=400, detail="Idempotency-Key header must contain at least eight characters")
    if not (services.case_root / payload.case_id / "manifest.json").is_file():
        raise HTTPException(status_code=404, detail=f"Unknown pinned case: {payload.case_id}")
    config = payload.model_dump(exclude={"case_id", "mode", "fixture_mode"}, exclude_none=True)
    try:
        run, _created = services.repository.create_run(
            case_id=payload.case_id,
            mode=payload.mode,
            fixture_mode=payload.fixture_mode,
            config=config,
            idempotency_key=idempotency_key.strip(),
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return _run_response(run)


def _run_response(run: RunSnapshot) -> RunResponse:
    return RunResponse(
        run_id=run.run_id,
        case_id=run.case_id,
        mode=run.mode,
        state=run.state,
        fixture_mode=run.fixture_mode,
        stage_attempt=run.stage_attempt,
        lease_owner=run.lease_owner,
        lease_expires_at=run.lease_expires_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def _error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "retryable": False,
                "details": {},
                "correlation_id": request.state.correlation_id,
            }
        },
    )
