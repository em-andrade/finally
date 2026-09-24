'use client';

import { ResponsiveContainer, Tooltip, Treemap } from 'recharts';
import type { Position } from '@/lib/types';
import { formatCurrency, formatPercent } from '@/lib/format';

interface PortfolioHeatmapProps {
  positions: Position[];
}

interface HeatmapNode {
  name: string;
  size: number;
  pnlPercent: number;
  marketValue: number;
}

function colorForPnl(pnlPercent: number): string {
  if (pnlPercent > 0) {
    const intensity = Math.min(1, pnlPercent / 15);
    return `rgba(34, 197, 94, ${0.25 + intensity * 0.6})`;
  }
  if (pnlPercent < 0) {
    const intensity = Math.min(1, Math.abs(pnlPercent) / 15);
    return `rgba(239, 68, 68, ${0.25 + intensity * 0.6})`;
  }
  return 'rgba(100, 116, 139, 0.35)';
}

export function HeatmapCell(props: any) {
  const { x, y, width, height, name, pnlPercent, depth } = props as HeatmapNode & {
    x: number;
    y: number;
    width: number;
    height: number;
    depth?: number;
  };
  // Recharts' Treemap also invokes `content` once for its own synthesized root
  // container (depth 0), which doesn't carry our leaf-level data props at all —
  // only actual position leaves (depth 1) have a defined pnlPercent.
  if (depth === 0 || typeof pnlPercent !== 'number') return null;
  if (width <= 0 || height <= 0) return null;
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{ fill: colorForPnl(pnlPercent), stroke: '#0d1117', strokeWidth: 2 }}
      />
      {width > 40 && height > 24 && (
        <text x={x + width / 2} y={y + height / 2} textAnchor="middle" fill="#e2e8f0" fontSize={12} dy={-2}>
          {name}
        </text>
      )}
      {width > 40 && height > 36 && (
        <text x={x + width / 2} y={y + height / 2} textAnchor="middle" fill="#cbd5e1" fontSize={10} dy={14}>
          {formatPercent(pnlPercent)}
        </text>
      )}
    </g>
  );
}

export default function PortfolioHeatmap({ positions }: PortfolioHeatmapProps) {
  const data: HeatmapNode[] = positions
    .filter((p) => p.market_value > 0)
    .map((p) => ({
      name: p.ticker,
      size: p.market_value,
      pnlPercent: p.unrealized_pl_percent,
      marketValue: p.market_value,
    }));

  return (
    <div className="panel flex h-full flex-col p-4">
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">Portfolio Heatmap</h2>
      <div className="flex-1">
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <Treemap data={data} dataKey="size" stroke="#0d1117" content={<HeatmapCell />} isAnimationActive={false}>
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid #30364a', fontSize: 12 }}
                formatter={(value: number, _name, item: any) => [
                  formatCurrency(value),
                  `${item?.payload?.name} (${formatPercent(item?.payload?.pnlPercent ?? 0)})`,
                ]}
              />
            </Treemap>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-600">
            No open positions yet.
          </div>
        )}
      </div>
    </div>
  );
}
