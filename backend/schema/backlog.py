from pydantic import BaseModel


class BacklogAging(BaseModel):
    lt_7d: int
    d7_to_30: int
    d30_to_90: int
    gt_90d: int
