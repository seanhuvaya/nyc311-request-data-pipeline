import { Cell, Pie, PieChart } from "recharts"
import { CircleAlert as AlertCircle } from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
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
import { useEffect, useState } from "react"
import { getBacklogAging } from "@/lib/api"
import type { BacklogAging } from "@/types"

const pieConfig = {
  lt_7d: { label: "< 7 Days", color: "var(--chart-1)" },
  d7_to_30: { label: "7–30 Days", color: "var(--chart-2)" },
  d30_to_90: { label: "30–90 Days", color: "var(--chart-3)" },
  gt_90d: { label: "90+ Days", color: "var(--chart-4)" },
} satisfies ChartConfig

export function BacklogPage() {
  const [data, setData] = useState<BacklogAging | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getBacklogAging()
      .then(setData)
      .catch((e) => console.error(e))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Loading backlog data...
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        No backlog data available.
      </div>
    )
  }

  const total = data.lt_7d + data.d7_to_30 + data.d30_to_90 + data.gt_90d

  const pieData = [
    { name: "lt_7d", value: data.lt_7d, fill: "var(--chart-1)" },
    { name: "d7_to_30", value: data.d7_to_30, fill: "var(--chart-2)" },
    { name: "d30_to_90", value: data.d30_to_90, fill: "var(--chart-3)" },
    { name: "gt_90d", value: data.gt_90d, fill: "var(--chart-4)" },
  ]

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Backlog &amp; Operations
        </h1>
        <p className="text-sm text-muted-foreground">
          Age distribution of currently open 311 requests
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Open &lt; 7 Days"
          value={data.lt_7d.toLocaleString()}
          subtitle={total > 0 ? `${((data.lt_7d / total) * 100).toFixed(1)}% of backlog` : "—"}
          icon={AlertCircle}
        />
        <MetricCard
          title="Open 7–30 Days"
          value={data.d7_to_30.toLocaleString()}
          subtitle={total > 0 ? `${((data.d7_to_30 / total) * 100).toFixed(1)}% of backlog` : "—"}
          icon={AlertCircle}
        />
        <MetricCard
          title="Open 30–90 Days"
          value={data.d30_to_90.toLocaleString()}
          subtitle={total > 0 ? `${((data.d30_to_90 / total) * 100).toFixed(1)}% of backlog` : "—"}
          icon={AlertCircle}
        />
        <MetricCard
          title="Open 90+ Days"
          value={data.gt_90d.toLocaleString()}
          subtitle={total > 0 ? `${((data.gt_90d / total) * 100).toFixed(1)}% of backlog` : "—"}
          icon={AlertCircle}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Backlog Age Distribution</CardTitle>
            <CardDescription>
              {total.toLocaleString()} total open requests
            </CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-center">
            <ChartContainer config={pieConfig} className="h-[280px] w-full max-w-[360px]">
              <PieChart>
                <ChartTooltip content={<ChartTooltipContent nameKey="name" />} />
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  innerRadius={48}
                  paddingAngle={2}
                >
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={entry.fill} />
                  ))}
                </Pie>
                <ChartLegend content={<ChartLegendContent nameKey="name" />} />
              </PieChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Aging Summary</CardTitle>
            <CardDescription>Breakdown of open request age buckets</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-4">
              {pieData.map((bucket) => (
                <div key={bucket.name} className="flex items-center gap-3">
                  <div
                    className="h-3 w-3 shrink-0 rounded-full"
                    style={{ backgroundColor: bucket.fill }}
                  />
                  <div className="flex-1">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">
                        {pieConfig[bucket.name as keyof typeof pieConfig].label}
                      </span>
                      <span>{bucket.value.toLocaleString()}</span>
                    </div>
                    <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: total > 0 ? `${(bucket.value / total) * 100}%` : "0%",
                          backgroundColor: bucket.fill,
                        }}
                      />
                    </div>
                  </div>
                  <span className="w-12 text-right text-xs text-muted-foreground">
                    {total > 0 ? `${((bucket.value / total) * 100).toFixed(1)}%` : "—"}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
