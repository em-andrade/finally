import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import Header from '@/components/Header';

describe('Header', () => {
  it('renders formatted portfolio value and cash balance', () => {
    render(<Header totalValue={12345.678} cashBalance={5000} status="connected" />);

    expect(screen.getByTestId('total-value')).toHaveTextContent('$12,345.68');
    expect(screen.getByTestId('cash-balance')).toHaveTextContent('$5,000.00');
  });

  it('renders a placeholder when values are not yet loaded', () => {
    render(<Header totalValue={null} cashBalance={null} status="disconnected" />);

    expect(screen.getByTestId('total-value')).toHaveTextContent('—');
    expect(screen.getByTestId('cash-balance')).toHaveTextContent('—');
  });

  it.each([
    ['connected', 'bg-up'],
    ['reconnecting', 'bg-accent-yellow'],
    ['disconnected', 'bg-down'],
  ] as const)('shows the %s status as %s', (status, expectedClass) => {
    render(<Header totalValue={0} cashBalance={0} status={status} />);
    expect(screen.getByTestId('status-dot')).toHaveClass(expectedClass);
  });
});
