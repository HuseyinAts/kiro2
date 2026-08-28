/**
 * OSBService Tests
 * OSB (Otizm Spektrum Bozukluğu) erişilebilirlik ayarları API sözleşmesi.
 * Servis camelCase <-> snake_case çevirisini sahiplenir; PUT tüm 16 alanı gönderir.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()

vi.mock('../apiClient', () => ({
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: (...args: unknown[]) => mockPut(...args),
  },
}))

const { osbService, DEFAULT_OSB_SETTINGS } = await import('../osbService')

// Full snake_case wire payload (backend OSBSettingsResponse — 16 fields + 4 meta)
const apiResponse = {
  id: 'osb-1',
  user_id: 'user-42',
  osb_mode_enabled: true,
  consistent_layout_enabled: true,
  layout_type: 'centered',
  predictable_elements: true,
  fixed_navigation_enabled: true,
  navigation_position: 'top',
  navigation_variant: 'horizontal',
  consistent_colors_enabled: true,
  theme_changes_disabled: true,
  high_contrast_mode: true,
  standard_icons_enabled: true,
  show_icon_labels: false,
  icon_size: '32',
  reduced_motion: false,
  no_animations: true,
  no_shadows: false,
  created_at: '2026-07-26T00:00:00Z',
  updated_at: '2026-07-26T00:00:00Z',
}

describe('OSBService', () => {
  beforeEach(() => {
    mockGet.mockReset()
    mockPost.mockReset()
    mockPut.mockReset()
  })

  it('getSettings maps snake_case response to camelCase', async () => {
    mockGet.mockResolvedValueOnce({ data: apiResponse })

    const result = await osbService.getSettings()

    expect(mockGet).toHaveBeenCalledWith('/api/v1/osb/settings/')
    expect(result).toEqual({
      id: 'osb-1',
      userId: 'user-42',
      osbModeEnabled: true,
      consistentLayoutEnabled: true,
      layoutType: 'centered',
      predictableElements: true,
      fixedNavigationEnabled: true,
      navigationPosition: 'top',
      navigationVariant: 'horizontal',
      consistentColorsEnabled: true,
      themeChangesDisabled: true,
      highContrastMode: true,
      standardIconsEnabled: true,
      showIconLabels: false,
      iconSize: '32',
      reducedMotion: false,
      noAnimations: true,
      noShadows: false,
      createdAt: '2026-07-26T00:00:00Z',
      updatedAt: '2026-07-26T00:00:00Z',
    })
  })

  it('updateSettings maps camelCase to snake_case and merges all 16 fields with defaults', async () => {
    mockPut.mockResolvedValueOnce({ data: apiResponse })

    // Caller touches ONLY one field — service must still PUT all 16.
    await osbService.updateSettings({ reducedMotion: false })

    expect(mockPut).toHaveBeenCalledTimes(1)
    const [url, body] = mockPut.mock.calls[0]
    expect(url).toBe('/api/v1/osb/settings/')

    // The touched field overrides the default; every other field is the default.
    expect(body).toEqual({
      osb_mode_enabled: true,
      consistent_layout_enabled: true,
      layout_type: 'default',
      predictable_elements: true,
      fixed_navigation_enabled: true,
      navigation_position: 'top',
      navigation_variant: 'horizontal',
      consistent_colors_enabled: true,
      theme_changes_disabled: true,
      high_contrast_mode: false,
      standard_icons_enabled: true,
      show_icon_labels: true,
      icon_size: '24',
      reduced_motion: false,
      no_animations: false,
      no_shadows: true,
    })
    // All 16 required fields present — never a partial PUT.
    expect(Object.keys(body)).toHaveLength(16)
  })

  it('updateSettings returns the camelCase-mapped server response', async () => {
    mockPut.mockResolvedValueOnce({ data: apiResponse })

    const result = await osbService.updateSettings({ highContrastMode: true })

    expect(result.highContrastMode).toBe(true)
    expect(result.userId).toBe('user-42')
  })

  it('applyPreset posts to the preset-specific URL', async () => {
    mockPost.mockResolvedValueOnce({ data: apiResponse })

    await osbService.applyPreset('full_osb')

    expect(mockPost).toHaveBeenCalledWith('/api/v1/osb/settings/apply-preset/full_osb')
  })

  it('resetSettings posts to /reset', async () => {
    mockPost.mockResolvedValueOnce({ data: { success: true, message: 'ok' } })

    const result = await osbService.resetSettings()

    expect(mockPost).toHaveBeenCalledWith('/api/v1/osb/settings/reset')
    expect(result.success).toBe(true)
  })

  it('DEFAULT_OSB_SETTINGS matches the backend request-model defaults', () => {
    expect(DEFAULT_OSB_SETTINGS.reducedMotion).toBe(true)
    expect(DEFAULT_OSB_SETTINGS.noShadows).toBe(true)
    expect(DEFAULT_OSB_SETTINGS.noAnimations).toBe(false)
    expect(DEFAULT_OSB_SETTINGS.highContrastMode).toBe(false)
    expect(DEFAULT_OSB_SETTINGS.iconSize).toBe('24')
    expect(Object.keys(DEFAULT_OSB_SETTINGS)).toHaveLength(16)
  })
})
