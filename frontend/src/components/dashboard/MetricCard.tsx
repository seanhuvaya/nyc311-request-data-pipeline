import { TrendingDown, TrendingUp, Minus } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  delta?: number
  deltaLabel?: string
  deltaInvert?: boolean
  icon?: React.ComponentType<{ className?: string }>
  className?: string
}

export function MetricCard({
  title,
  value,
  subtitle,
  delta,
  deltaLabel,
  deltaInvert = false,
  icon: Icon,
  className,
}: MetricCardProps) {
  const isPositive =
    delta !== undefined && (deltaInvert ? delta < 0 : delta > 0)
  const isNegative =
    delta !== undefined && (deltaInvert ? delta > 0 : delta < 0)
  const isNeutral = delta === 0

  return (
    <Card className={cn("gap-3", className)}>
      <CardHeader className="pb-0">
        <CardTitle className="flex items-center justify-between text-sm font-medium text-muted-foreground">
          <span>{title}</span>
          {Icon && (
            <div className="flex size-8 items-center justify-center rounded-md bg-muted">
              <Icon className="size-4 text-muted-foreground" />
            </div>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="text-2xl font-bold tracking-tight">{value}</div>
        {subtitle && (
          <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>
        )}
        {delta !== undefined && (
          <div className="mt-2 flex items-center gap-1">
            {isPositive && (
              <TrendingUp className="size-3.5 text-emerald-600 dark:text-emerald-500" />
            )}
            {isNegative && (
              <TrendingDown className="size-3.5 text-destructive" />
            )}
            {isNeutral && <Minus className="size-3.5 text-muted-foreground" />}
            <span
              className={cn(
                "text-xs font-medium",
                isPositive && "text-emerald-600 dark:text-emerald-500",
                isNegative && "text-destructive",
                isNeutral && "text-muted-foreground"
              )}
            >
              {delta > 0 ? "+" : ""}
              {delta}
              {deltaLabel ? ` ${deltaLabel}` : "%"}
            </span>
            <span className="text-xs text-muted-foreground">vs prev week</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
