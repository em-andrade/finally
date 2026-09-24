import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import PortfolioHeatmap, { HeatmapCell } from '@/components/PortfolioHeatmap';
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

describe('PortfolioHeatmap', () => {
  it('renders without crashing given a position', () => {
    expect(() => render(<PortfolioHeatmap positions={[position]} />)).not.toThrow();
  });

  it('shows an empty state with no positions', () => {
    const { getByText } = render(<PortfolioHeatmap positions={[]} />);
    expect(getByText(/no open positions/i)).toBeInTheDocument();
  });

  describe('HeatmapCell', () => {
    // Regression test: Recharts' <Treemap> invokes the custom `content` renderer
    // once for its own synthesized root container (depth 0), which carries none
    // of our leaf-level props (no pnlPercent). Previously this threw inside
    // formatPercent(undefined), white-screening the whole app on any trade.
    it('renders null for the Treemap root node without throwing', () => {
      expect(() =>
        HeatmapCell({ depth: 0, x: 0, y: 0, width: 400, height: 300 })
      ).not.toThrow();
      expect(HeatmapCell({ depth: 0, x: 0, y: 0, width: 400, height: 300 })).toBeNull();
    });

    it('renders null when pnlPercent is missing regardless of depth', () => {
      expect(HeatmapCell({ depth: 1, x: 0, y: 0, width: 100, height: 100, name: 'AAPL' })).toBeNull();
    });

    it('renders a cell for a real leaf node', () => {
      const cell = HeatmapCell({
        depth: 1,
        x: 0,
        y: 0,
        width: 100,
        height: 100,
        name: 'AAPL',
        pnlPercent: 5,
      });
      expect(cell).not.toBeNull();
    });
  });
});
