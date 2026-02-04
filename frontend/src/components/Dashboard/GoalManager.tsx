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
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Box,
  Fab,
  Divider
} from '@mui/material'
import {
  Add,
  Edit,
  Delete,
  Save,
  Cancel,
  Flag,
  TrendingUp,
  CheckCircle,
  Schedule
} from '@mui/icons-material'
import { dateUtils } from '@/utils/dateUtils'
import { Goal } from '../../types'
import { getGoals, createGoal, updateGoal, deleteGoal } from '../../api'

interface GoalManagerProps {
  open: boolean
  onClose: () => void
}

interface GoalFormData {
  baslik: string
  aciklama: string
  hedef_tipi: 'gunluk' | 'haftalik' | 'aylik'
  hedef_degeri: number
  baslangic_tarihi: string
  bitis_tarihi: string
}

const GOAL_TYPES = [
  { value: 'gunluk', label: 'Günlük', duration: 1 },
  { value: 'haftalik', label: 'Haftalık', duration: 7 },
  { value: 'aylik', label: 'Aylık', duration: 30 }
]

const GOAL_TEMPLATES = [
  {
    baslik: 'Günlük Çalışma',
    aciklama: 'Her gün belirli süre çalışmak',
    hedef_tipi: 'gunluk' as const,
    hedef_degeri: 120,
    unit: 'dakika'
  },
  {
    baslik: 'Haftalık Deneme Sınavı',
    aciklama: 'Her hafta deneme sınavı çözmek',
    hedef_tipi: 'haftalik' as const,
    hedef_degeri: 3,
    unit: 'sınav'
  },
  {
    baslik: 'Aylık Ders Tamamlama',
    aciklama: 'Ayda belirli sayıda ders tamamlamak',
    hedef_tipi: 'aylik' as const,
    hedef_degeri: 20,
    unit: 'ders'
  },
  {
    baslik: 'Sınav Ortalaması',
    aciklama: 'Sınavlarda belirli ortalama tutturmak',
    hedef_tipi: 'aylik' as const,
    hedef_degeri: 85,
    unit: '%'
  }
]

export function GoalManager({ open, onClose }: GoalManagerProps) {
  const [goals, setGoals] = useState<Goal[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null)
  const [saving, setSaving] = useState(false)

  const [formData, setFormData] = useState<GoalFormData>({
    baslik: '',
    aciklama: '',
    hedef_tipi: 'gunluk',
    hedef_degeri: 120,
    baslangic_tarihi: new Date().toISOString().split('T')[0],
    bitis_tarihi: dateUtils.addDays(new Date(), 30).toISOString().split('T')[0]
  })

  useEffect(() => {
    if (open) {
      loadGoals()
    }
  }, [open])

  const loadGoals = async () => {
    try {
      setLoading(true)
      setError(null)
      const goalsData = await getGoals(false) // Tüm hedefler
      setGoals(goalsData)
    } catch (err) {
      console.error('Hedefler yüklenirken hata:', err)
      setError('Hedefler yüklenirken bir hata oluştu')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateGoal = () => {
    setEditingGoal(null)
    setFormData({
      baslik: '',
      aciklama: '',
      hedef_tipi: 'gunluk',
      hedef_degeri: 120,
      baslangic_tarihi: new Date().toISOString().split('T')[0],
      bitis_tarihi: dateUtils.addDays(new Date(), 30).toISOString().split('T')[0]
    })
    setShowForm(true)
  }

  const handleEditGoal = (goal: Goal) => {
    setEditingGoal(goal)
    setFormData({
      baslik: goal.baslik,
      aciklama: goal.aciklama || '',
      hedef_tipi: goal.hedef_tipi as 'gunluk' | 'haftalik' | 'aylik',
      hedef_degeri: goal.hedef_degeri,
      baslangic_tarihi: goal.baslangic_tarihi.split('T')[0],
      bitis_tarihi: goal.bitis_tarihi.split('T')[0]
    })
    setShowForm(true)
  }

  const handleDeleteGoal = async (goalId: string) => {
    if (!confirm('Bu hedefi silmek istediğinizden emin misiniz?')) {
      return
    }

    try {
      await deleteGoal(goalId)
      setGoals(goals.filter(g => g.hedef_id !== goalId))
    } catch (err) {
      console.error('Hedef silinirken hata:', err)
      setError('Hedef silinirken bir hata oluştu')
    }
  }

  const handleSaveGoal = async () => {
    try {
      setSaving(true)
      setError(null)

      if (editingGoal) {
        // Güncelleme
        const updatedGoal = await updateGoal(editingGoal.hedef_id, {
          ...editingGoal,
          ...formData
        })
        setGoals(goals.map(g => g.hedef_id === editingGoal.hedef_id ? updatedGoal : g))
      } else {
        // Yeni oluşturma
        const newGoal = await createGoal(formData)
        setGoals([...goals, newGoal])
      }

      setShowForm(false)
      setEditingGoal(null)
    } catch (err) {
      console.error('Hedef kaydedilirken hata:', err)
      setError('Hedef kaydedilirken bir hata oluştu')
    } finally {
      setSaving(false)
    }
  }

  const handleTemplateSelect = (template: typeof GOAL_TEMPLATES[0]) => {
    const startDate = new Date()
    let endDate: Date

    switch (template.hedef_tipi) {
      case 'gunluk':
        endDate = dateUtils.addDays(startDate, 30) // 30 günlük hedef
        break
      case 'haftalik':
        endDate = dateUtils.addWeeks(startDate, 4) // 4 haftalık hedef
        break
      case 'aylik':
        endDate = dateUtils.addMonths(startDate, 3) // 3 aylık hedef
        break
    }

    setFormData({
      baslik: template.baslik,
      aciklama: template.aciklama,
      hedef_tipi: template.hedef_tipi,
      hedef_degeri: template.hedef_degeri,
      baslangic_tarihi: startDate.toISOString().split('T')[0],
      bitis_tarihi: endDate.toISOString().split('T')[0]
    })
  }

  const getGoalStatusColor = (goal: Goal) => {
    const progress = (goal.mevcut_deger / goal.hedef_degeri) * 100
    if (goal.durum === 'tamamlandi') return 'success'
    if (progress >= 80) return 'success'
    if (progress >= 50) return 'warning'
    return 'error'
  }

  const getGoalIcon = (type: string) => {
    switch (type) {
      case 'gunluk': return <Schedule />
      case 'haftalik': return <Flag />
      case 'aylik': return <Flag />
      default: return <Flag />
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <div className="flex items-center justify-between">
          <Typography variant="h5">Hedef Yönetimi</Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleCreateGoal}
          >
            Yeni Hedef
          </Button>
        </div>
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" className="mb-4">
            {error}
          </Alert>
        )}

        {loading ? (
          <Box className="flex items-center justify-center py-8">
            <CircularProgress />
          </Box>
        ) : (
          <Grid container spacing={3}>
            {goals.map((goal) => (
              <Grid item xs={12} sm={6} md={4} key={goal.hedef_id}>
                <Card>
                  <CardContent>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getGoalIcon(goal.hedef_tipi)}
                        <Typography variant="h6" className="flex-1">
                          {goal.baslik}
                        </Typography>
                      </div>
                      <div className="flex gap-1">
                        <IconButton
                          size="small"
                          onClick={() => handleEditGoal(goal)}
                        >
                          <Edit />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteGoal(goal.hedef_id)}
                        >
                          <Delete />
                        </IconButton>
                      </div>
                    </div>

                    <Typography variant="body2" color="textSecondary" className="mb-2">
                      {goal.aciklama}
                    </Typography>

                    <div className="flex items-center gap-2 mb-2">
                      <Chip
                        size="small"
                        label={GOAL_TYPES.find(t => t.value === goal.hedef_tipi)?.label}
                        color="primary"
                        variant="outlined"
                      />
                      <Chip
                        size="small"
                        label={goal.durum}
                        color={getGoalStatusColor(goal)}
                      />
                    </div>

                    <LinearProgress
                      variant="determinate"
                      value={Math.min((goal.mevcut_deger / goal.hedef_degeri) * 100, 100)}
                      className="mb-2"
                      color={getGoalStatusColor(goal)}
                    />

                    <div className="flex justify-between items-center mb-2">
                      <Typography variant="body2">
                        {goal.mevcut_deger} / {goal.hedef_degeri}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        %{Math.round((goal.mevcut_deger / goal.hedef_degeri) * 100)}
                      </Typography>
                    </div>

                    <Typography variant="caption" color="textSecondary">
                      {dateUtils.format(goal.baslangic_tarihi, 'DD MMM')} - {' '}
                      {dateUtils.format(goal.bitis_tarihi, 'DD MMM YYYY')}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}

            {goals.length === 0 && !loading && (
              <Grid item xs={12}>
                <Box className="text-center py-8">
                  <Flag className="text-6xl text-gray-400 mb-4" />
                  <Typography variant="h6" color="textSecondary" className="mb-2">
                    Henüz hedef belirlemediniz
                  </Typography>
                  <Typography variant="body2" color="textSecondary" className="mb-4">
                    İlk hedefinizi oluşturmak için "Yeni Hedef" butonuna tıklayın
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={handleCreateGoal}
                  >
                    İlk Hedefinizi Oluşturun
                  </Button>
                </Box>
              </Grid>
            )}
          </Grid>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Kapat</Button>
      </DialogActions>

      {/* Hedef Oluşturma/Düzenleme Formu */}
      <Dialog open={showForm} onClose={() => setShowForm(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingGoal ? 'Hedef Düzenle' : 'Yeni Hedef Oluştur'}
        </DialogTitle>

        <DialogContent>
          {!editingGoal && (
            <Box className="mb-4">
              <Typography variant="h6" className="mb-2">
                Hızlı Şablonlar
              </Typography>
              <Grid container spacing={2}>
                {GOAL_TEMPLATES.map((template, index) => (
                  <Grid item xs={12} sm={6} key={index}>
                    <Card 
                      className="cursor-pointer hover:bg-gray-50"
                      onClick={() => handleTemplateSelect(template)}
                    >
                      <CardContent className="py-2">
                        <Typography variant="subtitle2">
                          {template.baslik}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {template.hedef_degeri} {template.unit} - {template.aciklama}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
              <Divider className="my-4" />
            </Box>
          )}

          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Hedef Başlığı"
                value={formData.baslik}
                onChange={(e) => setFormData({ ...formData, baslik: e.target.value })}
                required
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Açıklama"
                value={formData.aciklama}
                onChange={(e) => setFormData({ ...formData, aciklama: e.target.value })}
                multiline
                rows={2}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Hedef Türü</InputLabel>
                <Select
                  value={formData.hedef_tipi}
                  onChange={(e) => setFormData({ 
                    ...formData, 
                    hedef_tipi: e.target.value as 'gunluk' | 'haftalik' | 'aylik'
                  })}
                  label="Hedef Türü"
                >
                  {GOAL_TYPES.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Hedef Değeri"
                value={formData.hedef_degeri}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  hedef_degeri: parseFloat(e.target.value) 
                })}
                required
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="date"
                label="Başlangıç Tarihi"
                value={formData.baslangic_tarihi}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  baslangic_tarihi: e.target.value 
                })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="date"
                label="Bitiş Tarihi"
                value={formData.bitis_tarihi}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  bitis_tarihi: e.target.value 
                })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
          </Grid>
        </DialogContent>

        <DialogActions>
          <Button
            onClick={() => setShowForm(false)}
            startIcon={<Cancel />}
            disabled={saving}
          >
            İptal
          </Button>
          <Button
            onClick={handleSaveGoal}
            variant="contained"
            startIcon={saving ? <CircularProgress size={20} /> : <Save />}
            disabled={saving || !formData.baslik || !formData.hedef_degeri}
          >
            {saving ? 'Kaydediliyor...' : 'Kaydet'}
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  )
}

export default GoalManager