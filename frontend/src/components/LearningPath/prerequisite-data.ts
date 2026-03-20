/**
 * YKS Matematik Prerequisite Graph — ALEKS KST modeli
 *
 * Directed Acyclic Graph (DAG) — her konu için önkoşul ilişkileri.
 * Vygotsky ZPD: Öğrenci prerequisite'leri tamamlamadan ileri konuya geçmemeli.
 */

export interface PrerequisiteNode {
  id: string;
  label: string;
  /** Prerequisite node ID'leri — bunlar tamamlanmadan bu node kilitli */
  prerequisites: string[];
  /** Kategori gruplaması */
  category: 'temel' | 'cebir' | 'geometri' | 'analiz' | 'sayma';
}

export const PREREQUISITE_GRAPH: PrerequisiteNode[] = [
  // Temel
  { id: 'sayi_kumeleri', label: 'Sayı Kümeleri', prerequisites: [], category: 'temel' },
  { id: 'dort_islem', label: 'Dört İşlem', prerequisites: ['sayi_kumeleri'], category: 'temel' },
  { id: 'uslu_sayilar', label: 'Üslü Sayılar', prerequisites: ['dort_islem'], category: 'temel' },
  { id: 'koklu_sayilar', label: 'Köklü Sayılar', prerequisites: ['uslu_sayilar'], category: 'temel' },

  // Cebir
  { id: 'cebirsel_ifadeler', label: 'Cebirsel İfadeler', prerequisites: ['dort_islem'], category: 'cebir' },
  { id: 'denklemler', label: 'Denklemler', prerequisites: ['cebirsel_ifadeler'], category: 'cebir' },
  { id: 'esitsizlikler', label: 'Eşitsizlikler', prerequisites: ['denklemler'], category: 'cebir' },
  { id: 'fonksiyonlar', label: 'Fonksiyonlar', prerequisites: ['denklemler', 'koordinat_sistemi'], category: 'cebir' },
  { id: 'polinomlar', label: 'Polinomlar', prerequisites: ['cebirsel_ifadeler', 'fonksiyonlar'], category: 'cebir' },
  { id: 'ikinci_derece', label: '2. Derece Denklemler', prerequisites: ['polinomlar'], category: 'cebir' },
  { id: 'logaritma', label: 'Logaritma', prerequisites: ['uslu_sayilar', 'fonksiyonlar'], category: 'cebir' },

  // Geometri
  { id: 'temel_geometri', label: 'Temel Geometri', prerequisites: ['dort_islem'], category: 'geometri' },
  { id: 'ucgenler', label: 'Üçgenler', prerequisites: ['temel_geometri'], category: 'geometri' },
  { id: 'koordinat_sistemi', label: 'Koordinat Sistemi', prerequisites: ['dort_islem'], category: 'geometri' },
  { id: 'dogru_denklemi', label: 'Doğru Denklemi', prerequisites: ['koordinat_sistemi', 'denklemler'], category: 'geometri' },
  { id: 'cember', label: 'Çember', prerequisites: ['ucgenler', 'koordinat_sistemi'], category: 'geometri' },
  { id: 'analitik_geometri', label: 'Analitik Geometri', prerequisites: ['dogru_denklemi', 'cember'], category: 'geometri' },

  // Analiz
  { id: 'diziler', label: 'Diziler', prerequisites: ['fonksiyonlar'], category: 'analiz' },
  { id: 'limit', label: 'Limit', prerequisites: ['fonksiyonlar', 'diziler'], category: 'analiz' },
  { id: 'sureklilik', label: 'Süreklilik', prerequisites: ['limit'], category: 'analiz' },
  { id: 'turev', label: 'Türev', prerequisites: ['limit', 'sureklilik'], category: 'analiz' },
  { id: 'integral', label: 'İntegral', prerequisites: ['turev'], category: 'analiz' },

  // Sayma / Olasılık
  { id: 'permutasyon', label: 'Permütasyon', prerequisites: ['dort_islem'], category: 'sayma' },
  { id: 'kombinasyon', label: 'Kombinasyon', prerequisites: ['permutasyon'], category: 'sayma' },
  { id: 'olasilik', label: 'Olasılık', prerequisites: ['kombinasyon'], category: 'sayma' },
];

export const CATEGORY_COLORS: Record<string, string> = {
  temel: '#6366f1',
  cebir: '#8b5cf6',
  geometri: '#3b82f6',
  analiz: '#ef4444',
  sayma: '#f59e0b',
};

export const CATEGORY_LABELS: Record<string, string> = {
  temel: 'Temel',
  cebir: 'Cebir',
  geometri: 'Geometri',
  analiz: 'Analiz',
  sayma: 'Sayma & Olasılık',
};
