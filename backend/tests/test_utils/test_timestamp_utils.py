"""
Tests for timestamp utilities.
"""

import pytest
from app.utils.timestamp_utils import seconds_to_mmss, mmss_to_seconds


def test_seconds_to_mmss():
    assert seconds_to_mmss(0) == "00:00"
    assert seconds_to_mmss(59) == "00:59"
    assert seconds_to_mmss(60) == "01:00"
    assert seconds_to_mmss(61) == "01:01"
    assert seconds_to_mmss(3599) == "59:59"
    assert seconds_to_mmss(3600) == "60:00"


def test_mmss_to_seconds():
    assert mmss_to_seconds("00:00") == 0
    assert mmss_to_seconds("00:59") == 59
    assert mmss_to_seconds("01:00") == 60
    assert mmss_to_seconds("01:01") == 61
    assert mmss_to_seconds("59:59") == 3599
    assert mmss_to_seconds("60:00") == 3600

    # Check single-digit components
    assert mmss_to_seconds("1:5") == 65

    # Invalid format should raise ValueError
    with pytest.raises(ValueError):
        mmss_to_seconds("invalid")
