/**
 * Otomatik Kaydetme Hook'u
 * Sınav cevaplarını periyodik olarak otomatik kaydetme
 */
import { useEffect, useRef, useCallback } from 'react'
import { examService } from '../services/examService'

interface UseAutoSaveOptions {
  sessionId: string
  enabled?: boolean
  interval?: number // milisaniye
  onSave?: (success: boolean, error?: string) => void
  onError?: (error: string) => void
}

interface SaveData {
  question_id: string
  selected_answer: string
  response_time?: number
}

export const useAutoSave = ({
  sessionId,
  enabled = true,
  interval = 30000, // 30 saniye
  onSave,
  onError
}: UseAutoSaveOptions) => {
  const saveQueueRef = useRef<Map<string, SaveData>>(new Map())
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const isSavingRef = useRef(false)
  const lastSaveTimeRef = useRef<Record<string, number>>({})

  /**
   * Kaydetme kuyruğuna ekle
   */
  const queueSave = useCallback((data: SaveData) => {
    if (!enabled) return

    // Aynı soru için önceki kaydetme zamanını kontrol et
    const now = Date.now()
    const lastSaveTime = lastSaveTimeRef.current[data.question_id] || 0
    
    // En az 1 saniye bekle (debounce)
    if (now - lastSaveTime < 1000) {
      return
    }

    saveQueueRef.current.set(data.question_id, {
      ...data,
      response_time: data.response_time || Math.floor((now - lastSaveTime) / 1000)
    })

    lastSaveTimeRef.current[data.question_id] = now
  }, [enabled])

  /**
   * Kuyruktaki tüm değişiklikleri kaydet
   */
  const processSaveQueue = useCallback(async () => {
    if (isSavingRef.current || saveQueueRef.current.size === 0) {
      return
    }

    isSavingRef.current = true
    const itemsToSave = Array.from(saveQueueRef.current.values())
    saveQueueRef.current.clear()

    try {
      // Batch kaydetme - tüm cevapları tek seferde gönder
      const savePromises = itemsToSave.map(item =>
        examService.saveAnswer(sessionId, item)
      )

      await Promise.all(savePromises)

      if (onSave) {
        onSave(true)
      }

      console.log(`✅ ${itemsToSave.length} cevap otomatik kaydedildi`)

    } catch (error: any) {
      console.error('❌ Otomatik kaydetme hatası:', error)
      
      // Başarısız olan kayıtları tekrar kuyruğa ekle
      itemsToSave.forEach(item => {
        saveQueueRef.current.set(item.question_id, iem)
      })

      const errorMessage = error.message || 'Otomatik kaydetme başarısız'
      
      if (onSave) {
        onSave(false, errorMessage)
      }
      
      if (onError) {
        onError(errorMessage)
      }
    } finally {
      isSavingRef.current = false
    }
  }, [sessionId, onSave, onError])

  /**
   * Manuel kaydetme
   */
  const saveNow = useCallback(async () => {
    await processSaveQueue()
  }, [processSaveQueue])

  /**
   * Belirli bir cevabı hemen kaydet
   */
  const saveImmediate = useCallback(async (data: SaveData) => {
    if (!enabled) return

    try {
      await examService.saveAnswer(sessionId, data)
      
      // Başarılı kaydetme sonrası kuyruktan kaldır
      saveQueueRef.current.delete(data.question_id)
      
      if (onSave) {
        onSave(true)
      }

      console.log(`✅ Cevap hemen kaydedildi: Soru ${data.question_id}`)

    } catch (error: any) {
      console.error('❌ Hemen kaydetme hatası:', error)
      
      // Başarısız olan kaydı kuyruğa ekle
      queueSave(data)
      
      const errorMessage = error.message || 'Cevap kaydedilemedi'
      
      if (onSave) {
        onSave(false, errorMessage)
      }
      
      if (onError) {
        onError(errorMessage)
      }
    }
  }, [enabled, sessionId, onSave, onError, queueSave])

  /**
   * Otomatik kaydetme interval'ini başlat
   */
  useEffect(() => {
    if (!enabled) return

    intervalRef.current = setInterval(() => {
      processSaveQueue()
    }, interval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [enabled, interval, processSaveQueue])

  /**
   * Sayfa kapatılırken son kaydetme
   */
  useEffect(() => {
    if (!enabled) return

    const handleBeforeUnload = async (event: BeforeUnloadEvent) => {
      if (saveQueueRef.current.size > 0) {
        event.preventDefault()
        event.returnValue = 'Kaydedilmemiş cevaplarınız var. Sayfayı kapatmak istediğinizden emin misiniz?'
        
        // Son bir kaydetme denemesi
        await processSaveQueue()
      }
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        // Sayfa gizlendiğinde kaydet
        processSaveQueue()
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [enabled, processSaveQueue])

  /**
   * Component unmount edilirken son kaydetme
   */
  useEffect(() => {
    return () => {
      if (saveQueueRef.current.size > 0) {
        processSaveQueue()
      }
    }
  }, [processSaveQueue])

  /**
   * Kaydetme durumu bilgileri
   */
  const getSaveStatus = useCallback(() => {
    return {
      pendingCount: saveQueueRef.current.size,
      isSaving: isSavingRef.current,
      lastSaveTimes: { ...lastSaveTimeRef.current }
    }
  }, [])

  /**
   * Kuyruğu temizle
   */
  const clearQueue = useCallback(() => {
    saveQueueRef.current.clear()
  }, [])

  return {
    queueSave,
    saveNow,
    saveImmediate,
    getSaveStatus,
    clearQueue,
    isEnabled: enabled
  }
}

export default useAutoSave