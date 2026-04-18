import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  XAxis,
  YAxis,
} from "recharts"
import {
  Activity,
  CircleCheck as CheckCircle,
  Clock,
  CircleAlert as AlertCircle,
} from "lucide-react"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { MetricCard } from "./MetricCard"
import { Badge } from "@/components/ui/badge"
import { useState, useEffect } from "react"

const areaChartConfig = {
  closed_requests: { label: "Closed", color: "var(--chart-2)" },
  open_requests: { label: "Open", color: "var(--chart-1)" },
} satisfies ChartConfig

const lineChartConfig = {
  avg_resolution_time_hours: {
    label: "Avg Resolution (hrs)",
    color: "var(--chart-3)",
  },
  median_resolution_time_hours: {
    label: "Median Resolution (hrs)",
    color: "var(--chart-4)",
  },
} satisfies ChartConfig

const closureChartConfig = {
  pct_closed: { label: "% Closed", color: "var(--chart-2)" },
} satisfies ChartConfig

type DailyMetric = {
  request_date: string
  closed_count: number
  open_count: number
  total_count: number
  avg_resolution_time_in_hours: number
  median_resolution_time_in_hours: number
  pct_closure_daily: number
}

type WeeklySummary = {
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

export function OverviewDashboard() {
  const [dailyData, setDailyData] = useState<DailyMetric[]>([])
  const [weeklySummary, setWeeklySummary] = useState<WeeklySummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dailyRes, weeklyRes] = await Promise.all([
          fetch(
            "https://api.nyc311.seanhuvaya.dev/api/v1/overview/30-day-summary"
          ),
          fetch(
            "https://api.nyc311.seanhuvaya.dev/api/v1/overview/weekly-summary"
          ),
        ])

        const daily: DailyMetric[] = await dailyRes.json()
        const weekly: WeeklySummary = await weeklyRes.json()

        setDailyData(daily)
        setWeeklySummary(weekly)
      } catch (error) {
        console.error("Failed to fetch NYC 311 data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // Prepare chart data
  const chartData = dailyData.map((d) => ({
    ...d,
    date: d.request_date.slice(5), // e.g., "04-18"
    closed_requests: d.closed_count,
    open_requests: d.open_count,
    pct_closed: d.pct_closure_daily,
    avg_resolution_time_hours: d.avg_resolution_time_in_hours,
    median_resolution_time_hours: d.median_resolution_time_in_hours,
  }))

  // Latest day (most recent)
  const latest = dailyData[dailyData.length - 1] || {
    closed_count: 0,
    total_count: 0,
    pct_closure_daily: 0,
    avg_resolution_time_in_hours: 0,
  }

  // Compute aggregates from weekly summary + daily data
  const totalLast7 = weeklySummary?.week_total_requests || 0
  const deltaRequests = weeklySummary?.prev_week_change_in_requests_pct || 0
  const deltaClosed =
    weeklySummary?.prev_week_change_in_closed_requests_pct || 0

  const avgRes =
    weeklySummary?.week_avg_resolution_time_in_hours?.toFixed(1) || "0"
  const deltaRes =
    weeklySummary?.prev_week_avg_resolution_time_in_hours_pct || 0

  const totalBacklog = dailyData.reduce((sum, day) => sum + day.open_count, 0)

  if (loading) {
    return <div className="p-8 text-center">Loading live 311 data...</div>
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Executive Overview
          </h1>
          <p className="text-sm text-muted-foreground">
            30-day operational summary — gold_311_requests_daily
          </p>
        </div>
        <Badge variant="secondary" className="gap-1.5">
          <span className="size-1.5 animate-pulse rounded-full bg-emerald-500" />
          Live •{" "}
          {new Date().toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
          })}
        </Badge>
      </div>

      {/* Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Requests (7d)"
          value={totalLast7.toLocaleString()}
          subtitle={`${latest.total_count.toLocaleString()} today`}
          delta={deltaRequests}
          deltaLabel="%"
          icon={Activity}
        />
        <MetricCard
          title="Closure Rate"
          value={`${latest.pct_closure_daily.toFixed(1)}%`}
          subtitle={`${latest.closed_count.toLocaleString()} closed today`}
          delta={deltaClosed}
          deltaLabel="pts"
          icon={CheckCircle}
        />
        <MetricCard
          title="Avg Resolution Time"
          value={`${avgRes}h`}
          subtitle="7-day rolling average"
          delta={deltaRes}
          deltaLabel="hrs"
          deltaInvert
          icon={Clock}
        />
        <MetricCard
          title="Open Backlog"
          value={totalBacklog.toLocaleString()}
          subtitle="Total unresolved requests"
          icon={AlertCircle}
        />
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Daily Request Volume</CardTitle>
            <CardDescription>
              Open vs closed requests over 30 days
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer
              config={areaChartConfig}
              className="h-[240px] w-full"
            >
              <AreaChart accessibilityLayer data={chartData}>
                <defs>
                  <linearGradient id="closedGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop
                      offset="5%"
                      stopColor="var(--chart-2)"
                      stopOpacity={0.3}
                    />
                    <stop
                      offset="95%"
                      stopColor="var(--chart-2)"
                      stopOpacity={0.05}
                    />
                  </linearGradient>
                  <linearGradient id="openGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop
                      offset="5%"
                      stopColor="var(--chart-1)"
                      stopOpacity={0.3}
                    />
                    <stop
                      offset="95%"
                      stopColor="var(--chart-1)"
                      stopOpacity={0.05}
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 11 }}
                  interval={4}
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                />
                <ChartTooltip
                  content={
                    <ChartTooltipContent labelKey="date" indicator="dot" />
                  }
                />
                <ChartLegend content={<ChartLegendContent />} />
                <Area
                  type="monotone"
                  dataKey="closed_requests"
                  stackId="1"
                  stroke="var(--chart-2)"
                  fill="url(#closedGrad)"
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey="open_requests"
                  stackId="1"
                  stroke="var(--chart-1)"
                  fill="url(#openGrad)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Closure Rate Trend</CardTitle>
            <CardDescription>% closed per day</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer
              config={closureChartConfig}
              className="h-[240px] w-full"
            >
              <LineChart accessibilityLayer data={chartData}>
                <CartesianGrid vertical={false} strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 11 }}
                  interval={7}
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 11 }}
                  domain={[0, 100]}
                  tickFormatter={(v) => `${v}%`}
                />
                <ChartTooltip
                  content={<ChartTooltipContent indicator="dot" />}
                />
                <Line
                  type="monotone"
                  dataKey="pct_closed"
                  stroke="var(--chart-2)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Resolution Time Trends</CardTitle>
          <CardDescription>
            Average and median resolution time in hours over 30 days
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={lineChartConfig} className="h-[200px] w-full">
            <LineChart accessibilityLayer data={chartData}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 11 }}
                interval={4}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `${v}h`}
              />
              <ChartTooltip
                content={<ChartTooltipContent indicator="line" />}
              />
              <ChartLegend content={<ChartLegendContent />} />
              <Line
                type="monotone"
                dataKey="avg_resolution_time_hours"
                stroke="var(--chart-3)"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="median_resolution_time_hours"
                stroke="var(--chart-4)"
                strokeWidth={2}
                dot={false}
                strokeDasharray="4 4"
              />
            </LineChart>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  )
}
