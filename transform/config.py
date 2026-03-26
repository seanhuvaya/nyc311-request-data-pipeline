from dataclasses import dataclass
from typing import List

COLUMNS_TO_DROP = [
    "vehicle_type", "descriptor_2", "taxi_pick_up_location", "bridge_highway_name",
    "bridge_highway_direction", "road_ramp", "bridge_highway_segment", "facility_type",
    "agency_name", "incident_address", "street_name", "cross_street_1", "cross_street_2",
    "intersection_street_1", "intersection_street_2", "park_borough", "location",
    "x_coordinate_state_plane", "y_coordinate_state_plane", "open_data_channel_type",
    "park_facility_name", "landmark", "bbl", "resolution_description",
    "resolution_action_updated_date"
]

FINAL_COLUMNS = [
    "unique_key", "created_date", "closed_date", "is_closed", "resolution_time",
    "agency", "complaint_type", "descriptor", "incident_zip", "address_type",
    "city", "status", "community_board", "council_district", "police_precinct",
    "borough", "latitude", "longitude", "location_type", "coord_imputation_source"
]


@dataclass
class TransformationConfig:
    columns_to_drop: List[str] = None
    final_columns: List[str] = None
    imputation_fallback: str = "UNKNOWN"

    def __post_init__(self):
        if self.columns_to_drop is None:
            self.columns_to_drop = COLUMNS_TO_DROP
        if self.final_columns is None:
            self.final_columns = FINAL_COLUMNS
