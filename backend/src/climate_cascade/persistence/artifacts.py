"""Immutable local content-addressed artifact storage."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import tempfile


@dataclass(frozen=True)
class StoredArtifact:
    sha256: str
    content_type: str
    byte_size: int
    storage_path: Path


class LocalArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def put_json(self, value: object) -> StoredArtifact:
        payload = (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")
        return self.put_bytes(payload, content_type="application/json")

    def put_bytes(self, payload: bytes, *, content_type: str) -> StoredArtifact:
        digest = sha256(payload).hexdigest()
        destination = self.root / "sha256" / digest[:2] / digest
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
                temporary.write(payload)
                temporary_path = Path(temporary.name)
            temporary_path.replace(destination)
        return StoredArtifact(digest, content_type, len(payload), destination)

    def read_json(self, artifact: StoredArtifact) -> object:
        return json.loads(artifact.storage_path.read_text(encoding="utf-8"))
