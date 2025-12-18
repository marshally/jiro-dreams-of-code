"""Parallel task execution module."""

from jiro.parallel.conflict_resolver import (
    ConflictResolver,
    ConflictStrategy,
    RecoveryAction,
    ResolutionResult,
)
from jiro.parallel.merger import (
    AggregatedResult,
    MergeResult,
    TaskResult,
    WorktreeMerger,
)
from jiro.parallel.scheduler import (
    ExecutingTask,
    TaskHandle,
    TaskScheduler,
    TaskStatus,
)
from jiro.parallel.worktree import WorktreeInfo, WorktreeManager

__all__ = [
    "AggregatedResult",
    "ConflictResolver",
    "ConflictStrategy",
    "ExecutingTask",
    "MergeResult",
    "RecoveryAction",
    "ResolutionResult",
    "TaskHandle",
    "TaskResult",
    "TaskScheduler",
    "TaskStatus",
    "WorktreeInfo",
    "WorktreeManager",
    "WorktreeMerger",
]
