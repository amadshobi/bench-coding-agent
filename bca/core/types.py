"""Core domain models, types, and data structures for BCA."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class Verdict(str, Enum):
    """Evaluation verdict of a trial."""
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"


class AgentStatus(str, Enum):
    """Execution status of an agent within a sandbox."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class SandboxMode(str, Enum):
    """Sandbox environment isolation mode."""
    SHADOW = "shadow"
    LOCAL = "local"
    DOCKER = "docker"


@dataclass(frozen=True)
class WildnessMetrics:
    """Telemetry tracking dangerous actions, blast radius, and out-of-bound attempts."""
    out_of_bounds_attempts: int = 0
    destructive_commands_detected: int = 0
    violation_log: List[str] = field(default_factory=list)
    safety_score: float = 100.0  # Starts at 100.0, penalized per violation


@dataclass(frozen=True)
class DiffStats:
    """Statistics of git diff modifications created by the agent."""
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    patch: str = ""


@dataclass(frozen=True)
class TokenUsage:
    """Token consumption and estimated cost."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    estimated_cost_idr: float = 0.0


@dataclass(frozen=True)
class QualityScore:
    """Judge Agent quality evaluation scores."""
    overall_quality: float = 0.0
    correctness: float = 0.0
    cleanliness: float = 0.0
    rule_compliance: float = 0.0
    efficiency: float = 0.0
    critique: str = ""


@dataclass(frozen=True)
class ExecutionMetrics:
    """Performance & efficiency metrics of an agent trial."""
    duration_seconds: float = 0.0
    setup_duration_seconds: float = 0.0
    agent_duration_seconds: float = 0.0
    verifier_duration_seconds: float = 0.0
    turn_count: int = 0
    tokens: TokenUsage = field(default_factory=TokenUsage)
    diff: DiffStats = field(default_factory=DiffStats)
    wildness: WildnessMetrics = field(default_factory=WildnessMetrics)
    quality: QualityScore = field(default_factory=QualityScore)
