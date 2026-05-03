/**
 * Layout regression tests — catch overflow/overlap issues.
 * Checks that components don't use conflicting height constraints.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import path from 'path'

const analysisPage = readFileSync(
  path.resolve(__dirname, '../../app/analysis/page.tsx'),
  'utf-8'
)

describe('analysis page layout', () => {
  it('OverviewPanel does not use h-full (causes overflow with siblings)', () => {
    const match = analysisPage.match(/function OverviewPanel[\s\S]*?^}/m)
    expect(match?.[0]).not.toContain('h-full')
  })

  it('both columns have min-h-0 for grid constraint', () => {
    // Left and right columns need min-h-0 so the grid can constrain height
    expect(analysisPage).toContain('min-h-0')
    expect(analysisPage).toContain('overflow-y-auto')
  })

  it('NotificationFeed is rendered in the left column', () => {
    const notifIdx = analysisPage.indexOf('<NotificationFeed')
    expect(notifIdx).toBeGreaterThan(-1)
    // Should be in the left column (before the right column tabs)
    const tabsIdx = analysisPage.indexOf('role="tablist"')
    expect(notifIdx).toBeLessThan(tabsIdx)
  })

  it('no card in OverviewPanel uses aspect ratio taller than 4/3', () => {
    const tallAspects = analysisPage.match(/aspect-\[(\d+)\/(\d+)\]/g) ?? []
    for (const match of tallAspects) {
      const [, w, h] = match.match(/aspect-\[(\d+)\/(\d+)\]/) ?? []
      const ratio = Number(w) / Number(h)
      expect(ratio).toBeLessThanOrEqual(4 / 3 + 0.01)
    }
  })
})
