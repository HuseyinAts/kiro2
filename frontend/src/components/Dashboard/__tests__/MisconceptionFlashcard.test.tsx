/**
 * MisconceptionFlashcard Component Tests
 */

import * as React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { screen } from '@testing-library/react'
import { render, renderWithUser } from '../../../test/utils/test-utils'
import { MisconceptionFlashcard } from '../MisconceptionFlashcard'

const defaultProps = {
  misconceptionName: 'İşlem Önceliği Hatası',
  distractor: 'Toplama her zaman çarpmadan önce yapılır sanılır.',
  refutation: 'Çarpma ve bölme, toplama ve çıkarmadan önce yapılır (BODMAS/PEMDAS).',
  takeaway: 'Önce parantez, üs, çarpma/bölme; sonra toplama/çıkarma.',
  onDismiss: vi.fn(),
}

describe('MisconceptionFlashcard', () => {
  it('renders the front side with the misconception name and distractor', () => {
    render(<MisconceptionFlashcard {...defaultProps} />)

    expect(screen.getByText('İşlem Önceliği Hatası')).toBeInTheDocument()
    expect(screen.getByText(/Toplama her zaman çarpmadan önce yapılır sanılır/)).toBeInTheDocument()
    expect(screen.getByText('KAVRAM YANILGISI TESPİT EDİLDİ')).toBeInTheDocument()
  })

  it('flips to the back side and shows the refutation + takeaway on click', async () => {
    const { user } = renderWithUser(<MisconceptionFlashcard {...defaultProps} />)

    await user.click(screen.getByText('Nasıl Düzeltilir? Görmek İçin Çevir'))

    expect(screen.getByText(defaultProps.refutation)).toBeInTheDocument()
    expect(screen.getByText(defaultProps.takeaway)).toBeInTheDocument()
  })

  it('calls onDismiss after the close button is clicked', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const onDismiss = vi.fn()
    const { user } = renderWithUser(<MisconceptionFlashcard {...defaultProps} onDismiss={onDismiss} />)

    // Close button is the small icon-only button next to the title.
    const closeButtons = screen.getAllByRole('button')
    await user.click(closeButtons[0])

    vi.advanceTimersByTime(500)
    expect(onDismiss).toHaveBeenCalledTimes(1)
    vi.useRealTimers()
  })
})
