import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import {
  MessageSquareWarning,
  CircleAlert as AlertCircle,
  Clock,
} from "lucide-react"
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
  type ChartConfig,
} from "@/components/ui/chart"
import { MetricCard } from "./MetricCard"
import { useEffect, useState } from "react"
import { getComplaintsSummary } from "@/lib/api"
import type { ComplaintTypeStat } from "@/types"

const barChartConfig = {
  total_count: { label: "Total Requests", color: "var(--chart-3)" },
} satisfies ChartConfig

export function ComplaintsPage() {
  const [data, setData] = useState<ComplaintTypeStat[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getComplaintsSummary()
      .then(setData)
      .catch((e) => console.error(e))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Loading complaint data...
      </div>
    )
  }

  const top10 = data.slice(0, 10)
  const top = data[0]
  const uniqueTypes = data.length
  const slowest = [...data]
    .filter((d) => d.p90_resolution_hours != null)
    .sort((a, b) => (b.p90_resolution_hours ?? 0) - (a.p90_resolution_hours ?? 0))[0]

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Complaint Trends</h1>
        <p className="text-sm text-muted-foreground">
          Request volume, closure rates, and resolution times by complaint type
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          title="Unique Complaint Types"
          value={uniqueTypes}
          subtitle="distinct categories"
          icon={MessageSquareWarning}
        />
        <MetricCard
          title="Top Complaint Type"
          value={top?.total_count.toLocaleString() ?? "—"}
          subtitle={top?.complaint_type ?? "—"}
          icon={AlertCircle}
        />
        <MetricCard
          title="Highest P90 Resolution"
          value={
            slowest?.p90_resolution_hours != null
              ? `${slowest.p90_resolution_hours.toFixed(0)}h`
              : "—"
          }
          subtitle={slowest?.complaint_type ?? "—"}
          icon={Clock}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Top 10 Complaint Types by Volume</CardTitle>
          <CardDescription>Total requests received</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={barChartConfig} className="h-[320px] w-full">
            <BarChart data={top10} layout="vertical" margin={{ left: 8 }}>
              <CartesianGrid horizontal={false} strokeDasharray="3 3" />
              <XAxis
                type="number"
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
              />
              <YAxis
                type="category"
                dataKey="complaint_type"
                width={140}
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 10 }}
              />
              <ChartTooltip content={<ChartTooltipContent indicator="dot" />} />
              <Bar
                dataKey="total_count"
                fill="var(--chart-3)"
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">All Complaint Types</CardTitle>
          <CardDescription>Sorted by total request volume</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 font-medium">Complaint Type</th>
                  <th className="pb-2 text-right font-medium">Total</th>
                  <th className="pb-2 text-right font-medium">Closed</th>
                  <th className="pb-2 text-right font-medium">% Closed</th>
                  <th className="pb-2 text-right font-medium">Avg Hrs</th>
                  <th className="pb-2 text-right font-medium">Median Hrs</th>
                  <th className="pb-2 text-right font-medium">P90 Hrs</th>
                </tr>
              </thead>
              <tbody>
                {data.map((row) => (
                  <tr
                    key={row.complaint_type}
                    className="border-b last:border-0 odd:bg-muted/30"
                  >
                    <td className="py-2 font-medium">{row.complaint_type}</td>
                    <td className="py-2 text-right">{row.total_count.toLocaleString()}</td>
                    <td className="py-2 text-right">{row.closed_count.toLocaleString()}</td>
                    <td className="py-2 text-right">{row.pct_closed.toFixed(1)}%</td>
                    <td className="py-2 text-right">
                      {row.avg_resolution_hours != null
                        ? row.avg_resolution_hours.toFixed(1)
                        : "—"}
                    </td>
                    <td className="py-2 text-right">
                      {row.median_resolution_hours != null
                        ? row.median_resolution_hours.toFixed(1)
                        : "—"}
                    </td>
                    <td className="py-2 text-right">
                      {row.p90_resolution_hours != null
                        ? row.p90_resolution_hours.toFixed(1)
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
