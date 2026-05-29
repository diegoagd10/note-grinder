from datetime import datetime

from src.clock import now


class TestNow:
    def test_returns_string(self):
        result = now()

        assert isinstance(result, str)

    def test_contains_date_time_separator(self):
        result = now()

        assert "T" in result

    def test_is_utc_indicated(self):
        result = now()

        has_utc_offset = "+00:00" in result
        has_z_suffix = result.endswith("Z")
        assert has_utc_offset or has_z_suffix, (
            f"Expected UTC indicator (+00:00 or Z) in timestamp, got: {result}"
        )

    def test_is_parseable_as_utc_datetime(self):
        result = now()

        # datetime.fromisoformat handles both '+00:00' and 'Z' (Python 3.11+)
        parsed = datetime.fromisoformat(result)
        assert parsed.tzinfo is not None, "Timestamp must be timezone-aware"
        assert parsed.utcoffset().total_seconds() == 0, (
            f"Timestamp must be UTC (offset=0), got offset: {parsed.utcoffset()}"
        )

    def test_successive_calls_are_monotonically_non_decreasing(self):
        first = datetime.fromisoformat(now())
        second = datetime.fromisoformat(now())

        assert second >= first, (
            f"Second call ({second}) must not be earlier than first call ({first})"
        )
