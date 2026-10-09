import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import Icon from '../src/components/common/Icon';

describe('Icon', () => {
  it('renders an inline decorative SVG that inherits its color', () => {
    const { container } = render(<Icon name="map" />);
    const svg = container.querySelector('svg');

    expect(svg).not.toBeNull();
    expect(svg).toHaveAttribute('aria-hidden', 'true');
    expect(svg).toHaveAttribute('focusable', 'false');
    expect(svg).toHaveAttribute('stroke', 'currentColor');
    expect(svg).toHaveAttribute('width', '18');
    expect(svg).toHaveAttribute('height', '18');
    expect(screen.queryByText('map')).not.toBeInTheDocument();
  });
});
