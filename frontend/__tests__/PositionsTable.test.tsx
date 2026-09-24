import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import PositionsTable from '@/components/PositionsTable';
import type { Position } from '@/lib/types';

const position: Position = {
  ticker: 'MSFT',
  quantity: 10,
  avg_cost: 300,
  current_price: 330,
  market_value: 3300,
  unrealized_pl: 300,
  unrealized_pl_percent: 10,
};

describe('PositionsTable', () => {
  it('renders position rows with computed P&L formatting and color', () => {
    render(<PositionsTable positions={[position]} />);

    const row = screen.getByTestId('position-MSFT');
    expect(row).toHaveTextContent('MSFT');
    expect(row).toHaveTextContent('10');
    expect(row).toHaveTextContent('300.00');
    expect(row).toHaveTextContent('330.00');
    expect(row).toHaveTextContent('$300.00');
    expect(row).toHaveTextContent('+10.00%');
  });

  it('colors a losing position red', () => {
    const losing: Position = {
      ...position,
      current_price: 270,
      unrealized_pl: -300,
      unrealized_pl_percent: -10,
    };
    render(<PositionsTable positions={[losing]} />);
    const pnlCell = screen.getByText('-$300.00');
    expect(pnlCell).toHaveClass('text-down');
  });

  it('shows an empty state with no positions', () => {
    render(<PositionsTable positions={[]} />);
    expect(screen.getByText(/no open positions/i)).toBeInTheDocument();
  });
});
