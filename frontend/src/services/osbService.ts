/**
 * OSB Settings Service — Otizm Spektrum Bozukluğu (OSB) erişilebilirlik ayarları
 * Backend: backend/api/osb_settings_api.py (prefix /api/v1/osb/settings)
 * Auth: httpOnly cookie (apiClient withCredentials)
 *
 * Bu servis camelCase <-> snake_case çevirisini SAHİPLENİR: uygulamaya
 * camelCase sunar, API'ye snake_case gönderir. PUT tüm 16 alanı ZORUNLU
 * ister; `updateSettings` eksik alanları DEFAULT_OSB_SETTINGS ile doldurur.
 * Çağıranlar dokunulmamış alanları clobber etmemek için önce mevcut ayarları
 * çekip (fetch) merge edip PUT etmelidir (fetch-merge-put).
 */

import apiClient from './apiClient';

export type OSBLayoutType = 'default' | 'centered' | 'wide';
export type OSBNavigationPosition = 'top' | 'left' | 'bottom';
export type OSBNavigationVariant = 'horizontal' | 'vertical';
export type OSBIconSize = '16' | '20' | '24' | '32' | '40' | '48';

/** PUT gövdesi — tüm 16 alan zorunlu (camelCase, uygulama tarafı). */
export interface OSBSettingsRequest {
  osbModeEnabled: boolean;
  // Layout
  consistentLayoutEnabled: boolean;
  layoutType: OSBLayoutType;
  predictableElements: boolean;
  // Navigation
  fixedNavigationEnabled: boolean;
  navigationPosition: OSBNavigationPosition;
  navigationVariant: OSBNavigationVariant;
  // Colors
  consistentColorsEnabled: boolean;
  themeChangesDisabled: boolean;
  highContrastMode: boolean;
  // Icons
  standardIconsEnabled: boolean;
  showIconLabels: boolean;
  iconSize: OSBIconSize;
  // Accessibility
  reducedMotion: boolean;
  noAnimations: boolean;
  noShadows: boolean;
}

/** GET/PUT yanıtı — request alanları + sunucu meta. */
export interface OSBSettings extends OSBSettingsRequest {
  id: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
}

export interface OSBPreset {
  id: string;
  name: string;
  description: string;
  settings: Record<string, unknown>;
}

export interface OSBPresetsResponse {
  presets: OSBPreset[];
}

/**
 * Backend request-model varsayılanları (osb_settings_api.py:36-63).
 * `updateSettings` partial payload'ı buradaki değerlerle tamamlar.
 */
export const DEFAULT_OSB_SETTINGS: OSBSettingsRequest = {
  osbModeEnabled: true,
  consistentLayoutEnabled: true,
  layoutType: 'default',
  predictableElements: true,
  fixedNavigationEnabled: true,
  navigationPosition: 'top',
  navigationVariant: 'horizontal',
  consistentColorsEnabled: true,
  themeChangesDisabled: true,
  highContrastMode: false,
  standardIconsEnabled: true,
  showIconLabels: true,
  iconSize: '24',
  reducedMotion: true,
  noAnimations: false,
  noShadows: true,
};

// --- snake_case wire şekilleri (backend sözleşmesi) ---
interface OSBSettingsRequestWire {
  osb_mode_enabled: boolean;
  consistent_layout_enabled: boolean;
  layout_type: string;
  predictable_elements: boolean;
  fixed_navigation_enabled: boolean;
  navigation_position: string;
  navigation_variant: string;
  consistent_colors_enabled: boolean;
  theme_changes_disabled: boolean;
  high_contrast_mode: boolean;
  standard_icons_enabled: boolean;
  show_icon_labels: boolean;
  icon_size: string;
  reduced_motion: boolean;
  no_animations: boolean;
  no_shadows: boolean;
}

interface OSBSettingsResponseWire extends OSBSettingsRequestWire {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

function toCamel(wire: OSBSettingsResponseWire): OSBSettings {
  return {
    id: wire.id,
    userId: wire.user_id,
    osbModeEnabled: wire.osb_mode_enabled,
    consistentLayoutEnabled: wire.consistent_layout_enabled,
    layoutType: wire.layout_type as OSBLayoutType,
    predictableElements: wire.predictable_elements,
    fixedNavigationEnabled: wire.fixed_navigation_enabled,
    navigationPosition: wire.navigation_position as OSBNavigationPosition,
    navigationVariant: wire.navigation_variant as OSBNavigationVariant,
    consistentColorsEnabled: wire.consistent_colors_enabled,
    themeChangesDisabled: wire.theme_changes_disabled,
    highContrastMode: wire.high_contrast_mode,
    standardIconsEnabled: wire.standard_icons_enabled,
    showIconLabels: wire.show_icon_labels,
    iconSize: wire.icon_size as OSBIconSize,
    reducedMotion: wire.reduced_motion,
    noAnimations: wire.no_animations,
    noShadows: wire.no_shadows,
    createdAt: wire.created_at,
    updatedAt: wire.updated_at,
  };
}

function toWire(req: OSBSettingsRequest): OSBSettingsRequestWire {
  return {
    osb_mode_enabled: req.osbModeEnabled,
    consistent_layout_enabled: req.consistentLayoutEnabled,
    layout_type: req.layoutType,
    predictable_elements: req.predictableElements,
    fixed_navigation_enabled: req.fixedNavigationEnabled,
    navigation_position: req.navigationPosition,
    navigation_variant: req.navigationVariant,
    consistent_colors_enabled: req.consistentColorsEnabled,
    theme_changes_disabled: req.themeChangesDisabled,
    high_contrast_mode: req.highContrastMode,
    standard_icons_enabled: req.standardIconsEnabled,
    show_icon_labels: req.showIconLabels,
    icon_size: req.iconSize,
    reduced_motion: req.reducedMotion,
    no_animations: req.noAnimations,
    no_shadows: req.noShadows,
  };
}

class OSBService {
  private baseURL = '/api/v1/osb/settings';

  /** Kullanıcının OSB ayarlarını getir (yoksa backend varsayılan oluşturur). */
  async getSettings(): Promise<OSBSettings> {
    const { data } = await apiClient.get<OSBSettingsResponseWire>(`${this.baseURL}/`);
    return toCamel(data);
  }

  /**
   * OSB ayarlarını güncelle. Backend tüm 16 alanı ister; verilmeyen alanlar
   * DEFAULT_OSB_SETTINGS ile tamamlanır. Dokunulmamış alanları korumak için
   * çağıran mevcut ayarları merge ederek göndermelidir (fetch-merge-put).
   */
  async updateSettings(payload: Partial<OSBSettingsRequest>): Promise<OSBSettings> {
    const full: OSBSettingsRequest = { ...DEFAULT_OSB_SETTINGS, ...payload };
    const { data } = await apiClient.put<OSBSettingsResponseWire>(
      `${this.baseURL}/`,
      toWire(full),
    );
    return toCamel(data);
  }

  /** OSB ayarlarını backend varsayılanına sıfırla. */
  async resetSettings(): Promise<{ success: boolean; message: string }> {
    const { data } = await apiClient.post<{ success: boolean; message: string }>(
      `${this.baseURL}/reset`,
    );
    return data;
  }

  /** Hazır OSB profillerini getir (kimlik doğrulaması gerekmez). */
  async getPresets(): Promise<OSBPresetsResponse> {
    const { data } = await apiClient.get<OSBPresetsResponse>(`${this.baseURL}/presets`);
    return data;
  }

  /** Hazır OSB profilini uygula ve güncel ayarları döndür. */
  async applyPreset(presetId: string): Promise<OSBSettings> {
    const { data } = await apiClient.post<OSBSettingsResponseWire>(
      `${this.baseURL}/apply-preset/${presetId}`,
    );
    return toCamel(data);
  }
}

export const osbService = new OSBService();
export default osbService;
