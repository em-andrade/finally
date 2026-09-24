'use client';

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { PricePoint } from '@/lib/useSSE';
import { formatPrice } from '@/lib/format';

interface MainChartProps {
  ticker: string | null;
  history: PricePoint[];
}

export default function MainChart({ ticker, history }: MainChartProps) {
  const data = history.map((point) => ({
    time: new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    price: point.price,
  }));

  return (
    <div className="panel flex h-full flex-col p-4">
      <div className="mb-2 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          {ticker ?? 'Select a ticker'}
        </h2>
        {ticker && data.length > 0 && (
          <span className="font-mono text-lg text-slate-100">{formatPrice(data[data.length - 1].price)}</span>
        )}
      </div>
      <div className="flex-1">
        {ticker && data.length > 1 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#209dd7" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#209dd7" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#30364a" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} minTickGap={40} />
              <YAxis
                stroke="#64748b"
                tick={{ fontSize: 10 }}
                domain={['auto', 'auto']}
                width={60}
              />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid #30364a', fontSize: 12 }}
                labelStyle={{ color: '#94a3b8' }}
              />
              <Area
                type="monotone"
                dataKey="price"
                stroke="#209dd7"
                fill="url(#priceFill)"
                strokeWidth={2}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-600">
            {ticker ? 'Waiting for price data…' : 'Click a ticker in the watchlist to view its chart.'}
          </div>
        )}
      </div>
    </div>
  );
}
