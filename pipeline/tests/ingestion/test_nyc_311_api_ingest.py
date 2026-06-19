from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from ingestion.nyc_311_api_ingest import extract_nyc311_requests_since


def _csv(*dates: str) -> str:
    return "created_date\n" + "".join(f"{d}\n" for d in dates)


def _response(text: str) -> MagicMock:
    r = MagicMock()
    r.text = text
    r.content = text.encode()
    r.raise_for_status = MagicMock()
    return r


@patch("ingestion.nyc_311_api_ingest.get_session_with_retry")
def test_empty_response_exits_immediately(mock_session_factory):
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
    s3.put_object.assert_not_called()
    assert session.get.call_count == 1


@patch("ingestion.nyc_311_api_ingest.get_session_with_retry")
def test_single_chunk_returns_max_date_and_uploads(mock_session_factory):
    session = MagicMock()
    session.get.side_effect = [
        _response(_csv("2024-01-05 10:00:00", "2024-01-03 08:00:00")),
        _response(_csv()),
    ]
    mock_session_factory.return_value = session
    s3 = MagicMock()

    result = extract_nyc311_requests_since(
        start_date=datetime(2024, 1, 1),
        s3_save_key="runs/daily",
        s3_client=s3,
    )

    assert result == datetime(2024, 1, 5, 10, 0, 0)
    s3.put_object.assert_called_once()
    kwargs = s3.put_object.call_args.kwargs
    assert kwargs["Key"] == "runs/daily/nyc311_requests_offset_0.csv"
    assert kwargs["ContentType"] == "text/csv"
    assert kwargs["Body"] == _csv("2024-01-05 10:00:00", "2024-01-03 08:00:00").encode()


@patch("ingestion.nyc_311_api_ingest.get_session_with_retry")
def test_multiple_chunks_tracks_global_max_date(mock_session_factory):
    session = MagicMock()
    session.get.side_effect = [
        _response(_csv("2024-01-05 10:00:00")),
        _response(_csv("2024-01-10 12:00:00")),
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
    assert s3.put_object.call_count == 2
    keys = [c.kwargs["Key"] for c in s3.put_object.call_args_list]
    assert keys == [
        "runs/daily/nyc311_requests_offset_0.csv",
        "runs/daily/nyc311_requests_offset_1.csv",
    ]


@patch("ingestion.nyc_311_api_ingest.get_session_with_retry")
def test_s3_failure_propagates_and_stops_loop(mock_session_factory):
    session = MagicMock()
    session.get.return_value = _response(_csv("2024-01-05 10:00:00"))
    mock_session_factory.return_value = session
    s3 = MagicMock()
    s3.put_object.side_effect = RuntimeError("connection refused")

    with pytest.raises(RuntimeError, match="connection refused"):
        extract_nyc311_requests_since(
            start_date=datetime(2024, 1, 1),
            s3_save_key="test/key",
            s3_client=s3,
        )

    assert session.get.call_count == 1


@patch("ingestion.nyc_311_api_ingest.get_session_with_retry")
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


@patch("ingestion.nyc_311_api_ingest.get_session_with_retry")
def test_session_created_once_not_per_chunk(mock_session_factory):
    session = MagicMock()
    session.get.side_effect = [
        _response(_csv("2024-01-05 10:00:00")),
        _response(_csv("2024-01-06 10:00:00")),
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
