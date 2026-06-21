import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { MapPin } from "lucide-react"
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
import { getBoroughSummary } from "@/lib/api"
import type { BoroughStat } from "@/types"

const barChartConfig = {
  total_count: { label: "Total", color: "var(--chart-1)" },
  closed_count: { label: "Closed", color: "var(--chart-2)" },
  open_count: { label: "Open", color: "var(--chart-3)" },
} satisfies ChartConfig

export function BoroughPage() {
  const [data, setData] = useState<BoroughStat[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getBoroughSummary()
      .then(setData)
      .catch((e) => console.error(e))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Loading borough data...
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Borough Breakdown</h1>
        <p className="text-sm text-muted-foreground">
          Request volume and resolution performance by NYC borough
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {data.map((borough) => (
          <MetricCard
            key={borough.borough}
            title={borough.borough}
            value={borough.total_count.toLocaleString()}
            subtitle={`${borough.pct_closed.toFixed(1)}% closed`}
            icon={MapPin}
          />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Requests by Borough</CardTitle>
          <CardDescription>Total, closed, and open counts per borough</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={barChartConfig} className="h-[280px] w-full">
            <BarChart data={data} barCategoryGap="30%">
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis
                dataKey="borough"
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 11 }}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
              />
              <ChartTooltip content={<ChartTooltipContent indicator="dot" />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Bar dataKey="total_count" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="closed_count" fill="var(--chart-2)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="open_count" fill="var(--chart-3)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Borough Summary</CardTitle>
          <CardDescription>All boroughs sorted by total request volume</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 font-medium">Borough</th>
                  <th className="pb-2 text-right font-medium">Total</th>
                  <th className="pb-2 text-right font-medium">Closed</th>
                  <th className="pb-2 text-right font-medium">Open</th>
                  <th className="pb-2 text-right font-medium">% Closed</th>
                  <th className="pb-2 text-right font-medium">Avg Hrs</th>
                  <th className="pb-2 text-right font-medium">Median Hrs</th>
                </tr>
              </thead>
              <tbody>
                {data.map((row) => (
                  <tr
                    key={row.borough}
                    className="border-b last:border-0 odd:bg-muted/30"
                  >
                    <td className="py-2 font-medium">{row.borough}</td>
                    <td className="py-2 text-right">{row.total_count.toLocaleString()}</td>
                    <td className="py-2 text-right">{row.closed_count.toLocaleString()}</td>
                    <td className="py-2 text-right">{row.open_count.toLocaleString()}</td>
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
