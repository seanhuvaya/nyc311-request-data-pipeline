"""Add new gold and dimension tables

Revision ID: 9d2a4c6e1b11
Revises: ec2cd253bbdd
Create Date: 2026-04-07 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9d2a4c6e1b11"
down_revision: Union[str, Sequence[str], None] = "ec2cd253bbdd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "gold_nyc311_requests_by_agency_daily",
        sa.Column("request_date", sa.Date(), nullable=False),
        sa.Column("agency", sa.String(), nullable=False),
        sa.Column("total_requests", sa.Integer(), nullable=False),
        sa.Column("open_requests", sa.Integer(), nullable=False),
        sa.Column("closed_requests", sa.Integer(), nullable=False),
        sa.Column("avg_resolution_time_in_hours", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("request_date", "agency", name="pk_gold_nyc311_request_date_agency"),
    )

    op.create_table(
        "gold_nyc311_requests_geo_daily",
        sa.Column("request_date", sa.Date(), nullable=False),
        sa.Column("borough", sa.String(), nullable=False),
        sa.Column("total_requests", sa.Integer(), nullable=False),
        sa.Column("closed_requests", sa.Integer(), nullable=False),
        sa.Column("avg_resolution_time_in_hours", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("request_date", "borough", name="pk_gold_nyc311_request_date_borough"),
    )

    op.create_table(
        "gold_nyc311_open_backlog_daily",
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("agency", sa.String(), nullable=False),
        sa.Column("borough", sa.String(), nullable=False),
        sa.Column("complaint_type", sa.String(), nullable=False),
        sa.Column("open_backlog_count", sa.Integer(), nullable=False),
        sa.Column("avg_age_open_hours", sa.Float(), nullable=True),
        sa.Column("max_age_open_hours", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint(
            "snapshot_date",
            "agency",
            "borough",
            "complaint_type",
            name="pk_gold_nyc311_snapshot_agency_borough_complaint",
        ),
    )

    op.create_table(
        "gold_nyc311_sla_performance_daily",
        sa.Column("request_date", sa.Date(), nullable=False),
        sa.Column("agency", sa.String(), nullable=False),
        sa.Column("complaint_type", sa.String(), nullable=False),
        sa.Column("total_closed_requests", sa.Integer(), nullable=False),
        sa.Column("closed_within_24h", sa.Integer(), nullable=False),
        sa.Column("closed_within_72h", sa.Integer(), nullable=False),
        sa.Column("closed_after_72h", sa.Integer(), nullable=False),
        sa.Column("pct_closed_within_24h", sa.Float(), nullable=False),
        sa.Column("pct_closed_within_72h", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint(
            "request_date",
            "agency",
            "complaint_type",
            name="pk_gold_nyc311_request_date_agency_complaint",
        ),
    )

    op.create_table(
        "gold_nyc311_top_complaints_monthly",
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("borough", sa.String(), nullable=False),
        sa.Column("complaint_type", sa.String(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column("rank_in_borough", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint(
            "month",
            "borough",
            "complaint_type",
            name="pk_gold_nyc311_month_borough_complaint",
        ),
    )

    op.create_table(
        "gold_nyc311_resolution_time_distribution",
        sa.Column("request_month", sa.Date(), nullable=False),
        sa.Column("agency", sa.String(), nullable=False),
        sa.Column("complaint_type", sa.String(), nullable=False),
        sa.Column("resolution_bucket", sa.String(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint(
            "request_month",
            "agency",
            "complaint_type",
            "resolution_bucket",
            name="pk_gold_nyc311_month_agency_complaint_bucket",
        ),
    )

    op.create_table(
        "gold_nyc311_location_hotspots",
        sa.Column("borough", sa.String(), nullable=False),
        sa.Column("incident_zip", sa.String(), nullable=False),
        sa.Column("complaint_type", sa.String(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column("avg_latitude", sa.Float(), nullable=True),
        sa.Column("avg_longitude", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint(
            "borough",
            "incident_zip",
            "complaint_type",
            name="pk_gold_nyc311_borough_zip_complaint",
        ),
    )

    op.create_table(
        "gold_nyc311_request_fact",
        sa.Column("unique_key", sa.Integer(), nullable=False),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_closed", sa.Boolean(), nullable=False),
        sa.Column("resolution_time_in_hours", sa.Float(), nullable=True),
        sa.Column("agency", sa.String(), nullable=False),
        sa.Column("complaint_type", sa.String(), nullable=False),
        sa.Column("descriptor", sa.String(), nullable=False),
        sa.Column("incident_zip", sa.String(), nullable=False),
        sa.Column("borough", sa.String(), nullable=False),
        sa.Column("community_board", sa.String(), nullable=False),
        sa.Column("council_district", sa.String(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("location_type", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("unique_key"),
    )

    op.create_table(
        "dim_date",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("month_name", sa.String(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("is_weekend", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("date"),
    )

    op.create_table(
        "dim_location",
        sa.Column("incident_zip", sa.String(), nullable=False),
        sa.Column("borough", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("community_board", sa.String(), nullable=False),
        sa.Column("council_district", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("incident_zip", "borough", name="pk_dim_location_zip_borough"),
    )

    op.create_table(
        "dim_complaint",
        sa.Column("complaint_type", sa.String(), nullable=False),
        sa.Column("descriptor", sa.String(), nullable=False),
        sa.Column("location_type", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint(
            "complaint_type",
            "descriptor",
            "location_type",
            name="pk_dim_complaint_type_descriptor_location",
        ),
    )

    op.create_table(
        "dim_agency",
        sa.Column("agency", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("agency"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("dim_agency")
    op.drop_table("dim_complaint")
    op.drop_table("dim_location")
    op.drop_table("dim_date")
    op.drop_table("gold_nyc311_request_fact")
    op.drop_table("gold_nyc311_location_hotspots")
    op.drop_table("gold_nyc311_resolution_time_distribution")
    op.drop_table("gold_nyc311_top_complaints_monthly")
    op.drop_table("gold_nyc311_sla_performance_daily")
    op.drop_table("gold_nyc311_open_backlog_daily")
    op.drop_table("gold_nyc311_requests_geo_daily")
    op.drop_table("gold_nyc311_requests_by_agency_daily")
