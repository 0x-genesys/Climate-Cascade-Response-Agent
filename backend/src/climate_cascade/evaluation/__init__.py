"""Deterministic evaluation contracts and scoring for frozen cases."""

from .scoring import BaselineEvaluationReport, CoverageAdjudication, evaluate_baseline

__all__ = ["BaselineEvaluationReport", "CoverageAdjudication", "evaluate_baseline"]
