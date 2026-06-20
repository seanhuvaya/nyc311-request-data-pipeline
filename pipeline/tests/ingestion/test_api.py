import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from nyc311.ingestion.api import extract_nyc311_requests_since


def _csv(*rows: tuple[str, str]) -> str:
    """
    Build a minimal CSV response. Each row is (created_date, resolution_action_updated_date).
    Pass an empty string for a null updated date.
    """
    body = "".join(f"{c},{u}\n" for c, u in rows)
    return f"created_date,resolution_action_updated_date\n{body}"


def _response(text: str) -> MagicMock:
    r = MagicMock()
    r.text = text
    r.content = text.encode()
    r.raise_for_status = MagicMock()
    return r


def _put_object_keys(s3_mock) -> list[str]:
    return [c.kwargs["Key"] for c in s3_mock.put_object.call_args_list]


@patch("nyc311.ingestion.api.get_session_with_retry")
def test_empty_response_saves_metadata_and_returns_start_date(mock_session_factory):
    session = MagicMock()
    session.get.return_value = _response(_csv())
    mock_session_factory.return_value = session
    s3 = MagicMock()

    result = extract_nyc311_requests_since(
        start_date=datetime(2024, 1, 1),
        s3_save_key="test/key",
        s3_client=s3,
    )

    assert result == datetime(2024, 1, 1)
    assert _put_object_keys(s3) == ["test/key/metadata.json"]


@patch("nyc311.ingestion.api.get_session_with_retry")
def test_watermark_uses_updated_date_when_present(mock_session_factory):
    session = MagicMock()
    session.get.side_effect = [
        _response(_csv(
            ("2024-01-03 08:00:00", "2024-01-05 10:00:00"),  # closed: updated > created
            ("2024-01-04 09:00:00", ""),                      # still open: no updated date
        )),
        _response(_csv()),
    ]
    mock_session_factory.return_value = session
    s3 = MagicMock()

    result = extract_nyc311_requests_since(
        start_date=datetime(2024, 1, 1),
        s3_save_key="runs/daily",
        s3_client=s3,
    )

    # Watermark should be max effective date = 2024-01-05 (from resolution_action_updated_date)
    assert result == datetime(2024, 1, 5, 10, 0, 0)


@patch("nyc311.ingestion.api.get_session_with_retry")
def test_late_arriving_closure_is_captured(mock_session_factory):
    # Record created 2024-01-01 (before the watermark) but closed on 2024-01-10 (after watermark).
    # The OR filter means it appears in this run; the effective date advances the watermark past
    # the closure date so the next run won't re-process it.
    session = MagicMock()
    session.get.side_effect = [
        _response(_csv(
            ("2024-01-10 09:00:00", ""),                      # new record, no closure yet
            ("2024-01-01 08:00:00", "2024-01-10 08:00:00"),  # old record, late closure
        )),
        _response(_csv()),
    ]
    mock_session_factory.return_value = session
    s3 = MagicMock()

    result = extract_nyc311_requests_since(
        start_date=datetime(2024, 1, 9),
        s3_save_key="runs/daily",
        s3_client=s3,
    )

    assert result == datetime(2024, 1, 10, 9, 0, 0)


@patch("nyc311.ingestion.api.get_session_with_retry")
def test_api_query_includes_or_filter_on_both_date_columns(mock_session_factory):
    session = MagicMock()
    session.get.return_value = _response(_csv())
    mock_session_factory.return_value = session
    s3 = MagicMock()

    extract_nyc311_requests_since(
        start_date=datetime(2024, 1, 1),
        s3_save_key="test/key",
        s3_client=s3,
    )

    url = session.get.call_args.args[0]
    assert "resolution_action_updated_date" in url
    assert "created_date" in url
    assert "OR" in url


@patch("nyc311.ingestion.api.get_session_with_retry")
def test_multiple_chunks_tracks_global_max_watermark(mock_session_factory):
    session = MagicMock()
    session.get.side_effect = [
        _response(_csv(("2024-01-05 10:00:00", ""))),
        _response(_csv(("2024-01-08 12:00:00", "2024-01-10 12:00:00"))),
        _response(_csv()),
    ]
    mock_session_factory.return_value = session
    s3 = MagicMock()

    result = extract_nyc311_requests_since(
        start_date=datetime(2024, 1, 1),
        s3_save_key="runs/daily",
        s3_client=s3,
        limit=1,
    )

    assert result == datetime(2024, 1, 10, 12, 0, 0)
    assert _put_object_keys(s3) == [
        "runs/daily/nyc311_requests_offset_0.csv",
        "runs/daily/nyc311_requests_offset_1.csv",
        "runs/daily/metadata.json",
    ]


@patch("nyc311.ingestion.api.get_session_with_retry")
def test_chunk_s3_failure_propagates_before_metadata_is_written(mock_session_factory):
    session = MagicMock()
    session.get.return_value = _response(_csv(("2024-01-05 10:00:00", "")))
    mock_session_factory.return_value = session
    s3 = MagicMock()
    s3.put_object.side_effect = RuntimeError("connection refused")

    with pytest.raises(RuntimeError, match="connection refused"):
        extract_nyc311_requests_since(
            start_date=datetime(2024, 1, 1),
            s3_save_key="test/key",
            s3_client=s3,
        )

    assert "test/key/metadata.json" not in _put_object_keys(s3)


@patch("nyc311.ingestion.api.get_session_with_retry")
def test_metadata_s3_failure_propagates(mock_session_factory):
    session = MagicMock()
    session.get.side_effect = [
        _response(_csv(("2024-01-05 10:00:00", ""))),
        _response(_csv()),
    ]
    mock_session_factory.return_value = session
    s3 = MagicMock()

    def _fail_on_metadata(**kwargs):
        if kwargs.get("Key", "").endswith("metadata.json"):
            raise RuntimeError("S3 write failed")

    s3.put_object.side_effect = _fail_on_metadata

    with pytest.raises(RuntimeError, match="S3 write failed"):
        extract_nyc311_requests_since(
            start_date=datetime(2024, 1, 1),
            s3_save_key="runs/daily",
            s3_client=s3,
        )


@patch("nyc311.ingestion.api.get_session_with_retry")
def test_timezone_aware_start_date_returns_naive(mock_session_factory):
    from zoneinfo import ZoneInfo
    session = MagicMock()
    session.get.return_value = _response(_csv())
    mock_session_factory.return_value = session
    s3 = MagicMock()

    result = extract_nyc311_requests_since(
        start_date=datetime(2024, 1, 1, tzinfo=ZoneInfo("America/New_York")),
        s3_save_key="test/key",
        s3_client=s3,
    )

    assert result.tzinfo is None


@patch("nyc311.ingestion.api.get_session_with_retry")
def test_metadata_json_content(mock_session_factory):
    session = MagicMock()
    session.get.side_effect = [
        _response(_csv(("2024-01-03 08:00:00", "2024-01-05 10:00:00"))),
        _response(_csv()),
    ]
    mock_session_factory.return_value = session
    s3 = MagicMock()

    extract_nyc311_requests_since(
        start_date=datetime(2024, 1, 1),
        s3_save_key="runs/daily",
        s3_client=s3,
    )

    metadata_call = next(
        c for c in s3.put_object.call_args_list
        if c.kwargs["Key"] == "runs/daily/metadata.json"
    )
    body = json.loads(metadata_call.kwargs["Body"])
    assert body["latest_watermark"] == "2024-01-05T10:00:00"
    assert body["total_records_fetched"] == 1000
    assert "updated_at" in body


@patch("nyc311.ingestion.api.get_session_with_retry")
def test_session_created_once_not_per_chunk(mock_session_factory):
    session = MagicMock()
    session.get.side_effect = [
        _response(_csv(("2024-01-05 10:00:00", ""))),
        _response(_csv(("2024-01-06 10:00:00", ""))),
        _response(_csv()),
    ]
    mock_session_factory.return_value = session
    s3 = MagicMock()

    extract_nyc311_requests_since(
        start_date=datetime(2024, 1, 1),
        s3_save_key="test/key",
        s3_client=s3,
        limit=1,
    )

    mock_session_factory.assert_called_once()
