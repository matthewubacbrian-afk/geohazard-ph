import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const testDirectory = dirname(fileURLToPath(import.meta.url));
const dashboardStyles = readFileSync(
  resolve(testDirectory, '../src/pages/Dashboard.module.css'),
  'utf8',
);
const sidebarStyles = readFileSync(
  resolve(testDirectory, '../src/components/dashboard/DashboardSidebar.module.css'),
  'utf8',
);

describe('dashboard desktop scrolling layout', () => {
  it('keeps the sidebar inside the viewport so its controls can scroll', () => {
    expect(dashboardStyles).toMatch(/\.main\s*\{[^}]*grid-template-rows:\s*minmax\(0,\s*1fr\)/s);
    expect(sidebarStyles).toMatch(/\.body\s*\{[^}]*overflow-y:\s*auto/s);
    expect(sidebarStyles).toMatch(/\.sidebar\s*\{[^}]*min-height:\s*0/s);
    expect(sidebarStyles).toMatch(/\.body\s*\{[^}]*min-height:\s*0/s);
  });
});
