'use client';

import { formatCurrency } from '@/lib/format';
import type { ConnectionStatus } from '@/lib/types';

interface HeaderProps {
  totalValue: number | null;
  cashBalance: number | null;
  status: ConnectionStatus;
}

const STATUS_CONFIG: Record<ConnectionStatus, { color: string; label: string }> = {
  connected: { color: 'bg-up', label: 'Connected' },
  reconnecting: { color: 'bg-accent-yellow', label: 'Reconnecting…' },
  disconnected: { color: 'bg-down', label: 'Disconnected' },
};

export default function Header({ totalValue, cashBalance, status }: HeaderProps) {
  const { color, label } = STATUS_CONFIG[status];

  return (
    <header className="flex items-center justify-between border-b border-border bg-base-800 px-6 py-3">
      <div className="flex items-center gap-3">
        <span className="text-lg font-bold tracking-tight text-accent-yellow">FinAlly</span>
        <span className="hidden text-xs text-slate-500 sm:inline">AI Trading Workstation</span>
      </div>

      <div className="flex items-center gap-6 font-mono text-sm">
        <div className="text-right">
          <div className="text-xs uppercase tracking-wide text-slate-500">Portfolio Value</div>
          <div className="text-base font-semibold text-slate-100" data-testid="total-value">
            {totalValue === null ? '—' : formatCurrency(totalValue)}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs uppercase tracking-wide text-slate-500">Cash</div>
          <div className="text-base font-semibold text-accent-blue" data-testid="cash-balance">
            {cashBalance === null ? '—' : formatCurrency(cashBalance)}
          </div>
        </div>
        <div className="flex items-center gap-2" role="status" aria-label={`Connection: ${label}`}>
          <span className={`h-2.5 w-2.5 rounded-full ${color}`} data-testid="status-dot" />
          <span className="hidden text-xs text-slate-500 md:inline">{label}</span>
        </div>
      </div>
    </header>
  );
}
