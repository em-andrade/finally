'use client';

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { PortfolioSnapshot } from '@/lib/types';
import { formatCurrency } from '@/lib/format';

interface PnLChartProps {
  snapshots: PortfolioSnapshot[];
}

export default function PnLChart({ snapshots }: PnLChartProps) {
  const data = snapshots.map((s) => ({
    time: new Date(s.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    value: s.total_value,
  }));

  return (
    <div className="panel flex h-full flex-col p-4">
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">Portfolio Value</h2>
      <div className="flex-1">
        {data.length > 1 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} minTickGap={30} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} domain={['auto', 'auto']} width={70} />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid #30364a', fontSize: 12 }}
                formatter={(value: number) => formatCurrency(value)}
              />
              <Line type="monotone" dataKey="value" stroke="#ecad0a" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-600">
            Not enough history yet.
          </div>
        )}
      </div>
    </div>
  );
}
