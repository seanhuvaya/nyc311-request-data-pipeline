import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { Building2, CircleAlert as AlertCircle, Clock } from "lucide-react"
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
import { getAgencyPerformance } from "@/lib/api"
import type { AgencyStat } from "@/types"

const barChartConfig = {
  total_count: { label: "Total Requests", color: "var(--chart-2)" },
} satisfies ChartConfig

export function AgencyPage() {
  const [data, setData] = useState<AgencyStat[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAgencyPerformance()
      .then(setData)
      .catch((e) => console.error(e))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading agency data...</div>
  }

  const top10 = data.slice(0, 10)
  const totalAgencies = data.length
  const avgClosure =
    data.length > 0
      ? (data.reduce((s, d) => s + d.pct_closed, 0) / data.length).toFixed(1)
      : "0"
  const totalOpenBacklog = data.reduce((s, d) => s + d.open_backlog, 0)

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Agency Performance</h1>
        <p className="text-sm text-muted-foreground">
          Closure rates and resolution times by responsible agency
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          title="Agencies Tracked"
          value={totalAgencies}
          subtitle="distinct agencies"
          icon={Building2}
        />
        <MetricCard
          title="Avg Closure Rate"
          value={`${avgClosure}%`}
          subtitle="across all agencies"
          icon={Clock}
        />
        <MetricCard
          title="Total Open Backlog"
          value={totalOpenBacklog.toLocaleString()}
          subtitle="unresolved requests"
          icon={AlertCircle}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Top 10 Agencies by Volume</CardTitle>
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
                dataKey="agency_code"
                width={72}
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 11 }}
              />
              <ChartTooltip content={<ChartTooltipContent indicator="dot" />} />
              <Bar
                dataKey="total_count"
                fill="var(--chart-2)"
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">All Agencies</CardTitle>
          <CardDescription>Sorted by total request volume</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 font-medium">Agency</th>
                  <th className="pb-2 text-right font-medium">Total</th>
                  <th className="pb-2 text-right font-medium">Closed</th>
                  <th className="pb-2 text-right font-medium">Open</th>
                  <th className="pb-2 text-right font-medium">% Closed</th>
                  <th className="pb-2 text-right font-medium">Avg Hrs</th>
                  <th className="pb-2 text-right font-medium">P90 Hrs</th>
                </tr>
              </thead>
              <tbody>
                {data.map((row) => (
                  <tr
                    key={row.agency_code}
                    className="border-b last:border-0 odd:bg-muted/30"
                  >
                    <td className="py-2 font-medium">{row.agency_code}</td>
                    <td className="py-2 text-right">{row.total_count.toLocaleString()}</td>
                    <td className="py-2 text-right">{row.closed_count.toLocaleString()}</td>
                    <td className="py-2 text-right">{row.open_backlog.toLocaleString()}</td>
                    <td className="py-2 text-right">{row.pct_closed.toFixed(1)}%</td>
                    <td className="py-2 text-right">
                      {row.avg_resolution_hours != null ? row.avg_resolution_hours.toFixed(1) : "—"}
                    </td>
                    <td className="py-2 text-right">
                      {row.p90_resolution_hours != null ? row.p90_resolution_hours.toFixed(1) : "—"}
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
