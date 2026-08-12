/**
 * 25 Uzman Denetimi — Adversarial İddia Doğrulama Workflow'u
 *
 * KOŞTURMA:  Claude'a "use a workflow: iddia-dogrulama" de, veya /iddia-dogrulama
 *
 * NEDEN WORKFLOW (rapor §A.5.4 + §D.1/#7):
 *  - Ara sonuçlar SCRIPT DEĞİŞKENLERİNDE kalır, ana bağlama girmez
 *  - pipeline() bariyersiz: U01 çürütmeye girerken U02 hâlâ doğrulanıyor olabilir
 *  - Aynı oturumda resume edilebilir; çok sayıda küçük ajan = daha çok korunan ilerleme
 *  - Adversarial verification yerleşik desen (§C.2.8)
 *
 * TASARIM KARARLARI (hepsi rapordan):
 *  - İKİ BAĞIMSIZ doğrulayıcı + anlaşmazlıkta 3. hakem (§C.2.8 "adversarial review")
 *  - Doğrulayıcılar sonnet, hakem opus (§D.1/#15: küçük uygular, büyük hakemlik eder)
 *  - Stakes dili SABİT (§C.6.1: %85,6 ↔ %16,7 kayması)
 *  - Sessiz kesme YOK: kapsam sınırlandıysa log() ile yaz (§A.5.4 "no silent caps")
 */

export const meta = {
  name: 'iddia-dogrulama',
  description: '25 uzman iddiasini iki bagimsiz cürütücü + 3. hakemle dogrular, fantomlari ayiklar',
  whenToUse: 'Bir denetim/panel bulgu listesinin hangilerinin gercek oldugunu olcmek gerektiginde',
  phases: [
    { title: 'Cürüt-A', detail: 'Her iddia icin 1. bagimsiz cürütücü' },
    { title: 'Cürüt-B', detail: 'Ayni iddia icin 2. bagimsiz cürütücü (A yi gormez)' },
    { title: 'Hakem', detail: 'Yalnizca A ve B anlasamazsa 3. hakem (opus)' },
    { title: 'Sentez', detail: 'Kütük yamasi + fantom orani raporu' },
  ],
}

// --- SABİT stakes dili. DEĞİŞTİRME. Rapor §C.6.1 ---------------------------
const STAKES =
  'Bu bir envanter dogrulamasidir. Bulgun ne olursa olsun kimse cezalandirilmaz ' +
  've hicbir sey silinmez; yalnizca kütüge yazilir.'

const KUTUK = 'docs/audits/2026-08-12_25uzman/iddialar.yaml'

const YARGI_SEMA = {
  type: 'object',
  required: ['id', 'yargi', 'severity_olculen', 'kanit', 'gerekce', 'fix_degeri'],
  properties: {
    id: { type: 'string' },
    yargi: { type: 'string', enum: ['dogrulandi', 'fantom', 'abartili', 'olculemedi'] },
    severity_olculen: { type: 'string', enum: ['P0', 'P1', 'P2', 'P3', 'yok'] },
    kanit: { type: 'string', description: 'Kostugun komut + GERCEK cikti. Kisaltma yok.' },
    curutme_zaten_kapali: { type: 'string' },
    curutme_yanlis_ad: { type: 'string' },
    curutme_baska_katman: { type: 'string' },
    curutme_semantik: { type: 'string' },
    gerekce: { type: 'string' },
    fix_degeri: { type: 'string', description: 'Olculebilir etki veya "bilinmiyor"' },
    kontrol_kolu_tuttu: { type: 'boolean' },
  },
}

const HAKEM_SEMA = {
  type: 'object',
  required: ['id', 'baglayici_yargi', 'severity_olculen', 'anlasmazlik_tipi', 'karar_gerekcesi'],
  properties: {
    id: { type: 'string' },
    baglayici_yargi: { type: 'string', enum: ['dogrulandi', 'fantom', 'abartili', 'olculemedi'] },
    severity_olculen: { type: 'string', enum: ['P0', 'P1', 'P2', 'P3', 'yok'] },
    anlasmazlik_tipi: {
      type: 'string',
      enum: ['farkli_katman', 'bayat_vs_canli', 'alet_arizasi', 'severity', 'gercek_belirsizlik'],
    },
    bagimsiz_olcum: { type: 'string' },
    kontrol_kolu: { type: 'string' },
    karar_gerekcesi: { type: 'string' },
    cozucu_olcum: { type: 'string' },
  },
}

// args ile alt küme koşulabilir: {ids:["U04","U13"]}  — yoksa hepsi
const HEDEFLER = (args && args.ids && args.ids.length)
  ? args.ids
  : ['U01','U02','U03','U04','U05','U06','U07','U08','U09','U10','U11','U12',
     'U13','U14','U15','U16','U17','U18','U19','U20','U21','U22','U23','U24','U25',
     'X05']   // X01-X04, X06 zaten dogrulandi — tekrar olcmeye deger yok

log(`${HEDEFLER.length} iddia dogrulanacak. Kütük: ${KUTUK}`)
if (args && args.ids) log(`KAPSAM SINIRLI: yalniz ${args.ids.join(', ')} — digerleri ATLANDI`)

function curutucuPrompt(id, mercek) {
  return `${STAKES}

Sen bir IDDIA CURUTUCUSUSUN. Gorevin dogrulamak DEGIL, CURUTMEYE calismaktir.
Curutemezsen iddia ayakta kalir.

KUTUK: ${KUTUK}
HEDEF IDDIA: ${id}
MERCEGIN: ${mercek}

ADIMLAR:
1. Kütükten "id: ${id}" girdisini oku. ankraj / iddia / curutme_sorusu /
   dogrulama / on_bulgu alanlarini al.
2. on_bulgu varsa ONU once sina — o bir hipotez, kanit degil.
3. dogrulama listesindeki HER komutu kostur. Ciktiyi sakla.
4. DORT CURUTME YOLU (hepsini dene, hepsini raporla):
   a) zaten kapali mi  -> git log --oneline -15 -- <dosya>, fix commit'i ara
   b) yanlis ad mi     -> esanlamli grep (invalidate/clear/evict, guard/gate/check)
   c) baska katmanda mi-> middleware, dependency, base class, decorator, config
   d) semantik yanlis mi-> iddia teknik olarak tutarli mi
5. KOD OKUYARAK KARAR VERME. Bir kontrolun korudugunu iddia ediyorsan
   ATLATMAYI DENE. Bir davranisin bozuk oldugunu iddia ediyorsan TETIKLE.
6. SEVERITY'yi AYRICA olc. severity_iddia ile ayni olmak zorunda degil.
   - var ama tetiklenemiyorsa -> duser
   - zaten genis marjli bir metrigi iyilestiriyorsa -> fix'in DEGERI yok
   - kusur degil modernizasyonsa -> P3
7. KONTROL KOLU: kullandigin olcum aleti bilinen-iyi bir ornekte beklenen
   sonucu veriyor mu? Vermiyorsa yargi ZORUNLU olarak "olculemedi".

YASAK: Write/Edit yok. "Muhtemelen" yok. Kanitsiz yargi yok.
Her yargi KOPYALANMIS GERCEK CIKTI tasimali.`
}

// FAZ 1+2+3: pipeline — bariyersiz. Bir iddia hakeme giderken digeri hala A'da.
const sonuclar = await pipeline(
  HEDEFLER,

  // Asama 1: Curutucu A — "zaten kapali / bayat mi" mercegi
  (id) =>
    agent(curutucuPrompt(id, 'BAYATLIK. Bu zaten duzeltilmis olabilir mi? git gecmisine ve kapali gorevlere agirlik ver.'), {
      label: `A:${id}`,
      phase: 'Cürüt-A',
      agentType: 'iddia-dogrulayici',
      schema: YARGI_SEMA,
    }),

  // Asama 2: Curutucu B — A'nin sonucunu GORMEZ (bagimsizlik sarti)
  (a, id) =>
    agent(curutucuPrompt(id, 'SEMANTIK + KATMAN. Iddia teknik olarak tutarli mi? Koruma/ozellik ust katmanda olabilir mi?'), {
      label: `B:${id}`,
      phase: 'Cürüt-B',
      agentType: 'iddia-dogrulayici',
      schema: YARGI_SEMA,
    }).then((b) => ({ id, a, b })),

  // Asama 3: Anlasmazlik varsa 3. hakem, yoksa gec
  async ({ id, a, b }) => {
    if (!a || !b) {
      log(`${id}: bir cürütücü dustu (a=${!!a} b=${!!b}) -> hakeme gidiyor`)
    } else if (a.yargi === b.yargi && a.severity_olculen === b.severity_olculen) {
      return { id, a, b, hakem: null, mutabakat: true, nihai: a.yargi, severity: a.severity_olculen }
    }
    const h = await agent(
      `${STAKES}

Sen UCUNCU HAKEMSIN. Iki bagimsiz cürütücü ${id} uzerinde ANLASAMADI.

CURUTUCU A: ${JSON.stringify(a)}
CURUTUCU B: ${JSON.stringify(b)}

KUTUK: ${KUTUK}

1. Anlasmazligi SINIFLANDIR: farkli_katman | bayat_vs_canli | alet_arizasi |
   severity | gercek_belirsizlik
2. KENDI BAGIMSIZ OLCUMUNU yap — sunulan kanitla yetinme. Ikisi de ayni kor
   noktaya dusmus olabilir.
3. KONTROL KOLUNU dogrula: aletin bilinen-iyi ornekte beklenen sonucu veriyor mu?
   Vermiyorsa iki tarafin kaniti da gecersizdir -> "olculemedi".
4. ORTALAMA ALMA. Hangi katmanin KULLANICIYA CIKTIGINI soyle.
5. "olculemedi" mesru bir karardir — o zaman COZUCU_OLCUM'u tarif et.`,
      { label: `hakem:${id}`, phase: 'Hakem', agentType: 'kanit-hakemi', effort: 'high', schema: HAKEM_SEMA },
    )
    return {
      id, a, b, hakem: h, mutabakat: false,
      nihai: h ? h.baglayici_yargi : 'olculemedi',
      severity: h ? h.severity_olculen : 'yok',
    }
  },
)

// FAZ 4: sentez — duz kod, ajan degil
const iyi = sonuclar.filter(Boolean)
const dusen = sonuclar.length - iyi.length
if (dusen > 0) log(`UYARI: ${dusen} iddia zincirde dustu, sonuca DAHIL EDILMEDI`)

const say = (y) => iyi.filter((r) => r.nihai === y).length
const ozet = {
  toplam_hedef: HEDEFLER.length,
  tamamlanan: iyi.length,
  dusen,
  dogrulandi: say('dogrulandi'),
  fantom: say('fantom'),
  abartili: say('abartili'),
  olculemedi: say('olculemedi'),
  mutabakatsiz: iyi.filter((r) => !r.mutabakat).length,
  fantom_orani: iyi.length ? +(say('fantom') / iyi.length * 100).toFixed(1) : null,
}

log(`SONUC: ${ozet.dogrulandi} gercek · ${ozet.fantom} fantom · ${ozet.abartili} abartili · ${ozet.olculemedi} olculemedi`)
log(`Fantom orani %${ozet.fantom_orani} (bu depoda tarihsel bant: %30-70)`)
log(`Cürütücüler ${ozet.mutabakatsiz} iddiada anlasamadi -> hakeme gitti`)

return {
  ozet,
  // Kütüge yazilacak yama — uygulamayi INSAN/ana oturum yapar, workflow degil
  kutuk_yamasi: iyi.map((r) => ({
    id: r.id,
    durum: r.nihai,
    severity_olculen: r.severity,
    kanit: r.hakem ? r.hakem.bagimsiz_olcum : (r.a && r.a.kanit),
    mutabakat: r.mutabakat,
    fix_degeri: r.a && r.a.fix_degeri,
  })),
  // P0/P1 cikan ve GERCEK olanlar — icra sirasi bundan turer
  once_bunlar: iyi
    .filter((r) => r.nihai === 'dogrulandi' && ['P0', 'P1'].includes(r.severity))
    .map((r) => r.id),
}
