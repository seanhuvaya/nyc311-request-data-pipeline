import logging

from utils.db import run_sql_statements
from utils.spark import load_to_postgres

logger = logging.getLogger(__name__)

from utils.db import get_db_engine

MERGE_REQUESTS_DAILY_SQL = """
                           INSERT INTO gold.nyc311_requests_daily AS g (unique_key,
                                                                        created_date,
                                                                        closed_date,
                                                                        date,
                                                                        agency,
                                                                        complaint_type,
                                                                        descriptor,
                                                                        community_board,
                                                                        incident_zip,
                                                                        location_type,
                                                                        address_type,
                                                                        city,
                                                                        borough,
                                                                        status,
                                                                        council_district,
                                                                        police_precinct,
                                                                        latitude,
                                                                        longitude,
                                                                        is_closed,
                                                                        resolution_time_in_hours)
                           SELECT s.unique_key,
                                  s.created_date,
                                  s.closed_date,
                                  s.date,
                                  s.agency,
                                  s.complaint_type,
                                  s.descriptor,
                                  s.community_board,
                                  s.incident_zip,
                                  s.location_type,
                                  s.address_type,
                                  s.city,
                                  s.borough,
                                  s.status,
                                  s.council_district,
                                  s.police_precinct,
                                  s.latitude,
                                  s.longitude,
                                  s.is_closed,
                                  s.resolution_time_in_hours
                           FROM staging.nyc311_requests_daily s
                           ON CONFLICT (unique_key) DO UPDATE
                               SET closed_date              = COALESCE(EXCLUDED.closed_date, g.closed_date),
                                   is_closed                = COALESCE(EXCLUDED.is_closed, g.is_closed),
                                   status                   = COALESCE(EXCLUDED.status, g.status),
                                   resolution_time_in_hours = COALESCE(
                                           EXCLUDED.resolution_time_in_hours,
                                           g.resolution_time_in_hours
                                                              ); \
                           """

MERGE_REQUESTS_DAILY_SUMMARY_SQL = """
                                   INSERT INTO gold.nyc311_requests_daily_summary AS g (request_date,
                                                                                        closed_count,
                                                                                        open_count,
                                                                                        avg_resolution_time_in_hours,
                                                                                        median_resolution_time_in_hours,
                                                                                        total_count,
                                                                                        pct_closure_daily)
                                   SELECT s.request_date,
                                          s.closed_count,
                                          s.open_count,
                                          s.avg_resolution_time_in_hours,
                                          s.median_resolution_time_in_hours,
                                          s.total_count,
                                          s.pct_closure_daily
                                   FROM staging.nyc311_requests_daily_summary s
                                   ON CONFLICT (request_date) DO UPDATE
                                       SET closed_count                    = COALESCE(EXCLUDED.closed_count, g.closed_count),
                                           open_count                      = COALESCE(EXCLUDED.open_count, g.open_count),
                                           avg_resolution_time_in_hours    = COALESCE(
                                                   EXCLUDED.avg_resolution_time_in_hours,
                                                   g.avg_resolution_time_in_hours
                                                                             ),
                                           median_resolution_time_in_hours = COALESCE(
                                                   EXCLUDED.median_resolution_time_in_hours,
                                                   g.median_resolution_time_in_hours
                                                                             ),
                                           total_count                     = COALESCE(EXCLUDED.total_count, g.total_count),
                                           pct_closure_daily               = COALESCE(
                                                   EXCLUDED.pct_closure_daily,
                                                   g.pct_closure_daily
                                                                             ); \
                                   """


def merge_requests_daily_to_gold() -> None:
    run_sql_statements(MERGE_REQUESTS_DAILY_SQL)


def merge_requests_daily_summary_to_gold() -> None:
    run_sql_statements(MERGE_REQUESTS_DAILY_SUMMARY_SQL)


def build_gold_nyc311_requests_daily() -> None:
    merge_requests_daily_to_gold()
    merge_requests_daily_summary_to_gold()
