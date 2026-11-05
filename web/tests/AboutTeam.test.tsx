import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import About from '../src/pages/About';

describe('About project and development team', () => {
  it('introduces the project goal and links to the working dashboard', () => {
    render(<About />);
    expect(screen.getByRole('heading', { name: 'Our purpose' })).toBeVisible();
    expect(screen.getByRole('link', { name: 'Explore the dashboard' })).toHaveAttribute('href', '/dashboard');
    expect(screen.getByText(/Philippine communities/)).toBeVisible();
    expect(screen.getByText('GeoHazard PH is not an official PHIVOLCS/NDRRMC advisory.')).toBeVisible();
  });
  it('pairs supplied portraits with the correct names and roles, with Matthew in the middle', () => {
    render(<About />);
    const team = screen.getByRole('region', { name: 'Meet the developers' });
    const cards = within(team).getAllByRole('article');
    const people = [
      ['Jet Justine D. Española', 'Lead Developer', 'jet-espanola'],
      ['Matthew Brian P. Ubac', 'Group Leader', 'matthew-ubac'],
      ['John Nathaniel B. Dizon', 'Project Manager', 'john-dizon'],
    ];
    expect(cards).toHaveLength(3);
    people.forEach(([name, role, file], index) => {
      expect(within(cards[index]).getByRole('heading', { name })).toBeVisible();
      expect(within(cards[index]).getByText(role)).toBeVisible();
      expect(within(cards[index]).getByRole('img', { name: `Portrait of ${name}` }))
        .toHaveAttribute('src', expect.stringContaining(file));
    });
    expect(within(cards[0]).getByText('Security')).toBeVisible();
    expect(within(cards[1]).getByText('API integration')).toBeVisible();
    expect(within(cards[2]).getByText('AI integration')).toBeVisible();
  });
});
