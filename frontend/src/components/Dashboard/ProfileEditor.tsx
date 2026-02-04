import React, { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Autocomplete
} from '@mui/material'
import { Save, Cancel } from '@mui/icons-material'
import { StudentProfile } from '../../types'
import { getStudentProfile, updateStudentProfile } from '../../api'

interface ProfileEditorProps {
  open: boolean
  onClose: () => void
  onSave: (profile: StudentProfile) => void
}

const TURKISH_UNIVERSITIES = [
  'İstanbul Teknik Üniversitesi',
  'Orta Doğu Teknik Üniversitesi',
  'Boğaziçi Üniversitesi',
  'İstanbul Üniversitesi',
  'Ankara Üniversitesi',
  'Hacettepe Üniversitesi',
  'Gazi Üniversitesi',
  'Ege Üniversitesi',
  'Dokuz Eylül Üniversitesi',
  'Marmara Üniversitesi',
  'Yıldız Teknik Üniversitesi',
  'Galatasaray Üniversitesi',
  'Koç Üniversitesi',
  'Sabancı Üniversitesi',
  'Bilkent Üniversitesi',
  'Özyeğin Üniversitesi',
  'Bahçeşehir Üniversitesi',
  'İstanbul Bilgi Üniversitesi',
  'Kadir Has Üniversitesi',
  'Akdeniz Üniversitesi',
  'Çukurova Üniversitesi',
  'Erciyes Üniversitesi',
  'Selçuk Üniversitesi',
  'Atatürk Üniversitesi',
  'Karadeniz Teknik Üniversitesi',
  'Ondokuz Mayıs Üniversitesi',
  'Uludağ Üniversitesi',
  'Anadolu Üniversitesi',
  'Pamukkale Üniversitesi',
  'Süleyman Demirel Üniversitesi'
]

const EXAM_TYPES = [
  { value: 'YKS', label: 'YKS (Yükseköğretim Kurumları Sınavı)' },
  { value: 'TYT', label: 'TYT (Temel Yeterlilik Testi)' },
  { value: 'AYT', label: 'AYT (Alan Yeterlilik Testi)' },
  { value: 'YDT', label: 'YDT (Yabancı Dil Testi)' }
]

const LEARNING_STYLES = [
  { value: 'GÖRSEL', label: 'Görsel Öğrenme' },
  { value: 'İŞİTSEL', label: 'İşitsel Öğrenme' },
  { value: 'OKUMA', label: 'Okuma/Yazma' },
  { value: 'KİNESTETİK', label: 'Kinestetik Öğrenme' },
  { value: 'HİBRİT', label: 'Hibrit (Karma)' }
]

const SUBJECT_AREAS = [
  'Matematik',
  'Türkçe',
  'Edebiyat',
  'Tarih',
  'Coğrafya',
  'Felsefe',
  'Fizik',
  'Kimya',
  'Biyoloji',
  'İngilizce',
  'Almanca',
  'Fransızca'
]

export function ProfileEditor({ open, onClose, onSave }: ProfileEditorProps) {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [profile, setProfile] = useState<StudentProfile | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    ad_soyad: '',
    telefon: '',
    sinif_seviyesi: 12,
    okul_adi: '',
    hedef_sinav: 'YKS',
    hedef_universiteler: [] as string[],
    ogrenme_stili: '',
    guclu_alanlar: [] as string[],
    zayif_alanlar: [] as string[],
    gunluk_calisma_hedefi: 120
  })

  useEffect(() => {
    if (open) {
      loadProfile()
    }
  }, [open])

  const loadProfile = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const profileData = await getStudentProfile()
      setProfile(profileData)
      
      // Form verilerini doldur
      setFormData({
        ad_soyad: '', // Bu backend'den gelecek
        telefon: '', // Bu backend'den gelecek
        sinif_seviyesi: profileData.sinif_seviyesi,
        okul_adi: profileData.okul_adi || '',
        hedef_sinav: profileData.hedef_sinav,
        hedef_universiteler: profileData.hedef_universiteler,
        ogrenme_stili: profileData.ogrenme_stili || '',
        guclu_alanlar: profileData.guclu_alanlar,
        zayif_alanlar: profileData.zayif_alanlar,
        gunluk_calisma_hedefi: profileData.gunluk_calisma_hedefi || 120
      })
      
    } catch (err) {
      console.error('Profil yüklenirken hata:', err)
      setError('Profil bilgileri yüklenirken bir hata oluştu')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      setError(null)

      // Sadece değişen alanları gönder
      const updateData: any = {}
      
      if (formData.ad_soyad) updateData.ad_soyad = formData.ad_soyad
      if (formData.telefon) updateData.telefon = formData.telefon
      if (formData.sinif_seviyesi !== profile?.sinif_seviyesi) {
        updateData.sinif_seviyesi = formData.sinif_seviyesi
      }
      if (formData.okul_adi !== profile?.okul_adi) {
        updateData.okul_adi = formData.okul_adi
      }
      if (JSON.stringify(formData.hedef_universiteler) !== JSON.stringify(profile?.hedef_universiteler)) {
        updateData.hedef_universiteler = formData.hedef_universiteler
      }
      if (formData.gunluk_calisma_hedefi !== profile?.gunluk_calisma_hedefi) {
        updateData.gunluk_calisma_hedefi = formData.gunluk_calisma_hedefi
      }

      const updatedProfile = await updateStudentProfile(updateData)
      onSave(updatedProfile)
      onClose()
      
    } catch (err) {
      console.error('Profil güncellenirken hata:', err)
      setError('Profil güncellenirken bir hata oluştu')
    } finally {
      setSaving(false)
    }
  }

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  if (loading) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogContent className="flex items-center justify-center py-8">
          <CircularProgress />
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Typography variant="h5">Profil Düzenle</Typography>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" className="mb-4">
            {error}
          </Alert>
        )}

        <Grid container spacing={3} className="mt-2">
          {/* Kişisel Bilgiler */}
          <Grid item xs={12}>
            <Typography variant="h6" className="mb-2">
              Kişisel Bilgiler
            </Typography>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Ad Soyad"
              value={formData.ad_soyad}
              onChange={(e) => handleInputChange('ad_soyad', e.target.value)}
              placeholder="Adınızı ve soyadınızı girin"
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Telefon"
              value={formData.telefon}
              onChange={(e) => handleInputChange('telefon', e.target.value)}
              placeholder="0555 123 45 67"
            />
          </Grid>

          {/* Eğitim Bilgileri */}
          <Grid item xs={12}>
            <Typography variant="h6" className="mb-2 mt-4">
              Eğitim Bilgileri
            </Typography>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Sınıf Seviyesi</InputLabel>
              <Select
                value={formData.sinif_seviyesi}
                onChange={(e) => handleInputChange('sinif_seviyesi', e.target.value)}
                label="Sınıf Seviyesi"
              >
                <MenuItem value={9}>9. Sınıf</MenuItem>
                <MenuItem value={10}>10. Sınıf</MenuItem>
                <MenuItem value={11}>11. Sınıf</MenuItem>
                <MenuItem value={12}>12. Sınıf</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Okul Adı"
              value={formData.okul_adi}
              onChange={(e) => handleInputChange('okul_adi', e.target.value)}
              placeholder="Okulunuzun adını girin"
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Hedef Sınav</InputLabel>
              <Select
                value={formData.hedef_sinav}
                onChange={(e) => handleInputChange('hedef_sinav', e.target.value)}
                label="Hedef Sınav"
              >
                {EXAM_TYPES.map((exam) => (
                  <MenuItem key={exam.value} value={exam.value}>
                    {exam.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              type="number"
              label="Günlük Çalışma Hedefi (dakika)"
              value={formData.gunluk_calisma_hedefi}
              onChange={(e) => handleInputChange('gunluk_calisma_hedefi', parseInt(e.target.value))}
              inputProps={{ min: 30, max: 600 }}
            />
          </Grid>

          {/* Hedef Üniversiteler */}
          <Grid item xs={12}>
            <Autocomplete
              multiple
              options={TURKISH_UNIVERSITIES}
              value={formData.hedef_universiteler}
              onChange={(_, newValue) => handleInputChange('hedef_universiteler', newValue)}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip
                    variant="outlined"
                    label={option}
                    {...getTagProps({ index })}
                    key={option}
                  />
                ))
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Hedef Üniversiteler"
                  placeholder="Üniversite seçin..."
                />
              )}
            />
          </Grid>

          {/* Öğrenme Özellikleri */}
          <Grid item xs={12}>
            <Typography variant="h6" className="mb-2 mt-4">
              Öğrenme Özellikleri
            </Typography>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Öğrenme Stili</InputLabel>
              <Select
                value={formData.ogrenme_stili}
                onChange={(e) => handleInputChange('ogrenme_stili', e.target.value)}
                label="Öğrenme Stili"
              >
                {LEARNING_STYLES.map((style) => (
                  <MenuItem key={style.value} value={style.value}>
                    {style.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Autocomplete
              multiple
              options={SUBJECT_AREAS}
              value={formData.guclu_alanlar}
              onChange={(_, newValue) => handleInputChange('guclu_alanlar', newValue)}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip
                    variant="outlined"
                    label={option}
                    color="success"
                    {...getTagProps({ index })}
                    key={option}
                  />
                ))
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Güçlü Alanlar"
                  placeholder="Güçlü olduğunuz konuları seçin..."
                />
              )}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <Autocomplete
              multiple
              options={SUBJECT_AREAS}
              value={formData.zayif_alanlar}
              onChange={(_, newValue) => handleInputChange('zayif_alanlar', newValue)}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip
                    variant="outlined"
                    label={option}
                    color="warning"
                    {...getTagProps({ index })}
                    key={option}
                  />
                ))
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Zayıf Alanlar"
                  placeholder="Geliştirilmesi gereken konuları seçin..."
                />
              )}
            />
          </Grid>
        </Grid>
      </DialogContent>
      
      <DialogActions className="p-4">
        <Button
          onClick={onClose}
          startIcon={<Cancel />}
          disabled={saving}
        >
          İptal
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          startIcon={saving ? <CircularProgress size={20} /> : <Save />}
          disabled={saving}
        >
          {saving ? 'Kaydediliyor...' : 'Kaydet'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ProfileEditor