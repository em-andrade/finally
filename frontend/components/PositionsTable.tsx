'use client';

import type { Position } from '@/lib/types';
import { formatCurrency, formatPercent, formatPrice, formatQuantity } from '@/lib/format';

interface PositionsTableProps {
  positions: Position[];
}

export default function PositionsTable({ positions }: PositionsTableProps) {
  return (
    <div className="panel flex h-full flex-col overflow-hidden">
      <h2 className="border-b border-border px-3 py-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Positions
      </h2>
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-base-800 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2 text-left">Ticker</th>
              <th className="px-3 py-2 text-right">Qty</th>
              <th className="px-3 py-2 text-right">Avg Cost</th>
              <th className="px-3 py-2 text-right">Price</th>
              <th className="px-3 py-2 text-right">P&amp;L</th>
              <th className="px-3 py-2 text-right">% Chg</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p) => (
              <tr key={p.ticker} className="border-b border-border/60" data-testid={`position-${p.ticker}`}>
                <td className="px-3 py-2 font-mono font-semibold text-slate-100">{p.ticker}</td>
                <td className="px-3 py-2 text-right font-mono">{formatQuantity(p.quantity)}</td>
                <td className="px-3 py-2 text-right font-mono">{formatPrice(p.avg_cost)}</td>
                <td className="px-3 py-2 text-right font-mono">{formatPrice(p.current_price)}</td>
                <td
                  className={`px-3 py-2 text-right font-mono ${p.unrealized_pl >= 0 ? 'text-up' : 'text-down'}`}
                >
                  {formatCurrency(p.unrealized_pl)}
                </td>
                <td
                  className={`px-3 py-2 text-right font-mono ${
                    p.unrealized_pl_percent >= 0 ? 'text-up' : 'text-down'
                  }`}
                >
                  {formatPercent(p.unrealized_pl_percent)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {positions.length === 0 && (
          <p className="px-3 py-4 text-center text-xs text-slate-600">No open positions.</p>
        )}
      </div>
    </div>
  );
}
