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
    // h-full on a flex child inside overflow-y-auto causes it to expand
    // beyond the scroll container, overlapping subsequent siblings
    const match = analysisPage.match(/function OverviewPanel[\s\S]*?^}/m)
    expect(match?.[0]).not.toContain('h-full')
  })

  it('both columns have min-h-0 and overflow-y-auto for independent scrolling', () => {
    // Each column needs both: min-h-0 lets the grid constrain height,
    // overflow-y-auto makes it scroll instead of expanding the page
    const leftCol = analysisPage.match(/Left:.*\n.*<div className="([^"]*)"/)
    const rightCol = analysisPage.match(/Right:.*\n.*<div className="([^"]*)"/)
    expect(leftCol?.[1]).toContain('min-h-0')
    expect(leftCol?.[1]).toContain('overflow-y-auto')
    expect(rightCol?.[1]).toContain('min-h-0')
    expect(rightCol?.[1]).toContain('overflow-y-auto')
  })

  it('EpisodeList and NotificationFeed are rendered after tab panel, not inside it', () => {
    // They should be siblings of the tab panel div, not children
    const episodeIdx = analysisPage.indexOf('<EpisodeList')
    const notifIdx = analysisPage.indexOf('<NotificationFeed')
    const renderPanelIdx = analysisPage.indexOf('{renderPanel()}')
    expect(episodeIdx).toBeGreaterThan(renderPanelIdx)
    expect(notifIdx).toBeGreaterThan(renderPanelIdx)
  })

  it('no card in OverviewPanel uses aspect ratio taller than 4/3', () => {
    // Tall aspect ratios (e.g. aspect-[8/5] = 1.6:1) push content below the fold
    const tallAspects = analysisPage.match(/aspect-\[(\d+)\/(\d+)\]/g) ?? []
    for (const match of tallAspects) {
      const [, w, h] = match.match(/aspect-\[(\d+)\/(\d+)\]/) ?? []
      const ratio = Number(w) / Number(h)
      expect(ratio).toBeLessThanOrEqual(4 / 3 + 0.01) // 4:3 max
    }
  })
})
