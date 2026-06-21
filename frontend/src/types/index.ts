export type NavPage =
  | "overview"
  | "agency"
  | "complaints"
  | "geo"
  | "backlog"
  | "sla"
  | "borough-heatmap"

export type DailyMetric = {
  request_date: string
  closed_count: number
  open_count: number
  total_count: number
  avg_resolution_time_in_hours: number
  median_resolution_time_in_hours: number
  pct_closure_daily: number
}

export type WeeklySummary = {
  week_start: string
  week_closed_requests: number
  week_total_requests: number
  week_closed_requests_pct: number
  week_avg_resolution_time_in_hours: number
  prev_week_total_requests: number
  prev_week_total_closed_requests: number
  prev_week_change_in_requests_pct: number
  prev_week_change_in_closed_requests_pct: number
  prev_week_avg_resolution_time_in_hours: number
  prev_week_avg_resolution_time_in_hours_pct: number
}

export type BoroughStat = {
  borough: string
  total_count: number
  closed_count: number
  open_count: number
  pct_closed: number
  avg_resolution_hours: number | null
  median_resolution_hours: number | null
}

export type ComplaintTypeStat = {
  complaint_type: string
  total_count: number
  closed_count: number
  pct_closed: number
  avg_resolution_hours: number | null
  median_resolution_hours: number | null
  p90_resolution_hours: number | null
}

export type AgencyStat = {
  agency_code: string
  total_count: number
  closed_count: number
  open_backlog: number
  pct_closed: number
  avg_resolution_hours: number | null
  p90_resolution_hours: number | null
}

export type DayOfWeekStat = {
  day_of_week: number
  day_name: string
  total_count: number
  pct_closed: number
  avg_resolution_hours: number | null
}

export type BacklogAging = {
  lt_7d: number
  d7_to_30: number
  d30_to_90: number
  gt_90d: number
}
