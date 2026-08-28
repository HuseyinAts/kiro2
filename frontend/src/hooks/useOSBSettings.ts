/**
 * useOSBSettings — OSB erişilebilirlik ayarları için React Query hook'u
 *
 * osbService üzerinden backend'e bağlanır (httpOnly cookie auth). Başarılı
 * her okuma/yazmada OSB CSS sınıflarını document.documentElement'e uygular:
 *   reduced-motion / no-animations / no-shadows / high-contrast
 * (accessibility.css bu sınıflarla animasyon/gölge/kontrast davranışını değiştirir;
 * useAccessibilitySettings ile aynı sınıf adları kullanılır).
 */

import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  osbService,
  type OSBSettings,
  type OSBSettingsRequest,
} from '../services/osbService';

export const osbSettingsKeys = {
  all: ['osb-settings'] as const,
};

/**
 * OSB ayarlarını DOM'a uygula. Alan adları useAccessibilitySettings /
 * SensoryControl orphan'larının hâlihazırda toggle ettiği sınıflarla eşleşir.
 */
export function applyOSBSettingsToDOM(settings: OSBSettings): void {
  const root = document.documentElement;
  root.classList.toggle('reduced-motion', settings.reducedMotion);
  root.classList.toggle('no-animations', settings.noAnimations);
  root.classList.toggle('no-shadows', settings.noShadows);
  root.classList.toggle('high-contrast', settings.highContrastMode);
}

export function useOSBSettings() {
  const queryClient = useQueryClient();

  const query = useQuery<OSBSettings>({
    queryKey: osbSettingsKeys.all,
    queryFn: () => osbService.getSettings(),
    staleTime: 5 * 60 * 1000, // 5 dakika
    retry: 1,
    onSuccess: (data) => applyOSBSettingsToDOM(data),
  });

  const applyResult = (data: OSBSettings) => {
    queryClient.setQueryData(osbSettingsKeys.all, data);
    applyOSBSettingsToDOM(data);
    queryClient.invalidateQueries({ queryKey: osbSettingsKeys.all });
  };

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<OSBSettingsRequest>) => osbService.updateSettings(payload),
    onSuccess: applyResult,
  });

  const resetMutation = useMutation({
    mutationFn: () => osbService.resetSettings(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: osbSettingsKeys.all });
    },
  });

  const applyPresetMutation = useMutation({
    mutationFn: (presetId: string) => osbService.applyPreset(presetId),
    onSuccess: applyResult,
  });

  return {
    settings: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,

    updateSettings: updateMutation.mutate,
    updateSettingsAsync: updateMutation.mutateAsync,
    isUpdating: updateMutation.isLoading,

    resetSettings: resetMutation.mutate,
    isResetting: resetMutation.isLoading,

    applyPreset: applyPresetMutation.mutate,
    isApplyingPreset: applyPresetMutation.isLoading,
  };
}

export default useOSBSettings;
