import pytest

from core import ClipRequest, normalize_timestamp, parse_timestamp


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1:00", 60), ("1:30", 90), ("00:05", 5), ("1:02:03", 3723), ("90:00", 5400)],
)
def test_parse_timestamp(value, expected):
    assert parse_timestamp(value) == expected


@pytest.mark.parametrize("value", ["", "1", "1:60", "x:10", "1:2:70", "1:2:3:4"])
def test_invalid_timestamp(value):
    with pytest.raises(ValueError):
        parse_timestamp(value)


def test_normalize_timestamp():
    assert normalize_timestamp(3723) == "01:02:03"


def test_end_must_be_after_start(tmp_path):
    with pytest.raises(ValueError, match="final"):
        ClipRequest.create("https://youtu.be/abc", "1:30", "1:00", tmp_path)
