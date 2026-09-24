'use client';

import { Line, LineChart, ResponsiveContainer, YAxis } from 'recharts';
import type { PricePoint } from '@/lib/useSSE';

interface SparklineProps {
  history: PricePoint[];
  direction: 'up' | 'down' | 'flat';
  width?: number;
  height?: number;
}

const COLORS = {
  up: '#22c55e',
  down: '#ef4444',
  flat: '#64748b',
};

export default function Sparkline({ history, direction, height = 32 }: SparklineProps) {
  if (history.length < 2) {
    return <div style={{ height }} className="w-24 text-xs text-slate-600" aria-hidden="true" />;
  }

  return (
    <div style={{ height }} className="w-24" data-testid="sparkline">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={history}>
          <YAxis domain={['dataMin', 'dataMax']} hide />
          <Line
            type="monotone"
            dataKey="price"
            stroke={COLORS[direction]}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
