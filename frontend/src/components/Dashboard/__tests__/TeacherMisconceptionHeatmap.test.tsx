/**
 * TeacherMisconceptionHeatmap Component Tests
 *
 * Not: recharts'in ResponsiveContainer'i jsdom altinda gercek layout
 * hesaplamadigi icin (0x0 boyut) SVG ic gorselleri (Scatter noktalari)
 * bu ortamda guvenilir sekilde dogrulanamiyor -- bu yuzden testler
 * component'in disinda kalan statik metne odaklaniyor.
 */

import * as React from 'react'
import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import { render } from '../../../test/utils/test-utils'
import { TeacherMisconceptionHeatmap } from '../TeacherMisconceptionHeatmap'

describe('TeacherMisconceptionHeatmap', () => {
  it('renders without crashing and shows the section title', () => {
    render(<TeacherMisconceptionHeatmap />)

    expect(screen.getByText('Sınıf Kavram Yanılgısı (Heatmap)')).toBeInTheDocument()
    expect(
      screen.getByText('BKT motoru tarafından tespit edilen çeldirici yoğunluk haritası.')
    ).toBeInTheDocument()
  })
})
