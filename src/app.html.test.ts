import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

// The plain-text copy of the page in app.html is for crawlers and agents only. It must never be
// painted, not even for a frame before the app mounts, and the app must never touch it.
const html = readFileSync(new URL('./app.html', import.meta.url), 'utf8');
const read = (p: string): string => readFileSync(new URL(`../static/${p}`, import.meta.url), 'utf8');

describe('app.html plain-text copy', () => {
  const open = html.match(/<article id="about-plain"[^>]*>/)?.[0] ?? '';

  it('is hidden by attribute and by an inline style, which outranks stylesheet rules', () => {
    expect(open).toContain(' hidden');
    expect(open).toContain('style="display: none"');
  });

  it('sits outside the element the app mounts into', () => {
    const mount = html.indexOf('%sveltekit.body%</div>');
    expect(mount).toBeGreaterThan(-1);
    expect(html.indexOf('<article id="about-plain"')).toBeGreaterThan(mount);
  });

  it('carries parseable JSON-LD', () => {
    const ld = html.match(/<script type="application\/ld\+json">(.*?)<\/script>/s)?.[1] ?? '';
    expect(() => JSON.parse(ld)).not.toThrow();
  });
});

describe('crawler files', () => {
  it('robots.txt points at the sitemap and llms.txt', () => {
    const robots = read('robots.txt');
    expect(robots).toContain('Sitemap: https://simulacraamericana.com/sitemap.xml');
    expect(robots).toContain('https://simulacraamericana.com/llms.txt');
  });

  it('llms.txt and the plain-text copy quote the same evaluation figures', () => {
    const llms = read('llms.txt');
    for (const figure of ['RMSE 7.6 points', '8.7 for uniform swing', '0.052', '0.069', 'Turnout RMSE 2.9']) {
      expect(llms).toContain(figure);
      expect(html).toContain(figure);
    }
  });
});
