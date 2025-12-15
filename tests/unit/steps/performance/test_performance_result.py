"""Tests for PerformanceResult dataclass."""

from pathlib import Path

from jiro.results.base import Result
from jiro.steps.performance.performance_result import PerformanceResult


class TestPerformanceResultIsResult:
    """Test that PerformanceResult is a proper Result subclass."""

    def test_is_result_subclass(self):
        """PerformanceResult should inherit from Result."""
        assert issubclass(PerformanceResult, Result)

    def test_can_instantiate(self):
        """Should be able to instantiate PerformanceResult."""
        result = PerformanceResult(
            changed_files=[Path("src/cache.py")],
            test_specifier="tests/test_cache.py::test_performance",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude-opus-4.5",
            subagent_prompt="Test prompt",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.5,
        )
        assert isinstance(result, PerformanceResult)
        assert result.test_specifier == "tests/test_cache.py::test_performance"


class TestPerformanceResultAttributes:
    """Test PerformanceResult attributes."""

    def test_has_changed_files(self):
        """Should have changed_files attribute."""
        result = PerformanceResult(
            changed_files=[Path("src/cache.py"), Path("src/query.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        assert len(result.changed_files) == 2
        assert Path("src/cache.py") in result.changed_files

    def test_test_specifier(self):
        """Should track test specifier."""
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_memory_usage",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        assert result.test_specifier == "tests/test_perf.py::test_memory_usage"

    def test_test_output(self):
        """Should track test output."""
        test_output_text = "passed in 0.5s"
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output=test_output_text,
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        assert result.test_output == test_output_text

    def test_benchmark_data_optional(self):
        """Should allow benchmark_data to be None."""
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        assert result.benchmark_data is None

    def test_benchmark_data_with_value(self):
        """Should allow benchmark_data to have a value."""
        benchmark = "cache_hits: 95%, latency_reduced: 40%"
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=benchmark,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        assert result.benchmark_data == benchmark

    def test_subagent_metrics(self):
        """Should track subagent metrics."""
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude-opus-4.5",
            subagent_prompt="Test prompt",
            tokens_in=1234,
            tokens_out=567,
            subagent_time=2.5,
        )
        assert result.subagent_type == "claude-opus-4.5"
        assert result.tokens_in == 1234
        assert result.tokens_out == 567
        assert result.subagent_time == 2.5


class TestPerformanceResultSerialization:
    """Test serialization methods inherited from Result."""

    def test_as_dict(self):
        """Should convert to dictionary."""
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        d = result.as_dict()
        assert isinstance(d, dict)
        assert d["test_specifier"] == "tests/test_perf.py::test_speed"
        assert d["changed_files"] == ["src/optimize.py"]

    def test_as_json(self):
        """Should convert to JSON."""
        result = PerformanceResult(
            changed_files=[Path("src/optimize.py")],
            test_specifier="tests/test_perf.py::test_speed",
            test_output="PASSED",
            benchmark_data=None,
            subagent_type="claude",
            subagent_prompt="test",
            tokens_in=100,
            tokens_out=50,
            subagent_time=1.0,
        )
        json_str = result.as_json()
        assert isinstance(json_str, str)
        assert "test_specifier" in json_str
        assert "tests/test_perf.py::test_speed" in json_str
