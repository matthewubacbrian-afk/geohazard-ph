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
  it('stacks the activity panel below the map at tablet widths and keeps controls scrollable', () => {
    expect(dashboardStyles).toMatch(/grid-template-rows:\s*minmax\(520px,\s*1fr\)\s+minmax\(320px,/s);
    expect(sidebarStyles).toMatch(/\.body\s*\{[^}]*overflow-y:\s*auto/s);
    expect(sidebarStyles).toMatch(/\.sidebar\s*\{[^}]*min-height:\s*0/s);
    expect(sidebarStyles).toMatch(/\.body\s*\{[^}]*min-height:\s*0/s);
  });
});
