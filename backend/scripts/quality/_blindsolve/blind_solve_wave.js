export const meta = {
  name: 'blind-solve-calib-420',
  description: 'Calibration: blind-solve 420 unverified candidates (40/agent), measure batch-blind quality + AGREE',
  phases: [{ title: 'Solve', detail: '420 questions, 40/agent, WAVE=3, no answer key' }],
}
const batches = args
function prompt(b) {
  return `Sen uzman bir YKS cozücüsün. Asagidaki dosyadaki HER soruyu DIKKATLICE coz ve dogru sikki bul.
ADIM 1: Su JSON dosyasini OKU (Read arac): ${b.file}
Yapi: {"questions":[{"id","q","a","b","c","d","e"},...]} (${b.n} soru). CEVAP ANAHTARI VERILMEDI - kendin cozeceksin.
ADIM 2: HER soruyu coz. Matematik/fizik/kimya icin hesapla, sozel icin metni analiz et. Emin degilsen en olasi sikki sec.
CIKTI: HER soru icin TAM bir satir, ${b.n} satir. Format:
id|CEVAP(A/B/C/D/E)|confidence(0-1)
Baska hicbir sey yazma. Sadece ${b.n} satir.`
}
const WAVE = 3
const all = []
for (let i = 0; i < batches.length; i += WAVE) {
  const chunk = batches.slice(i, i + WAVE)
  log(`Wave ${Math.floor(i / WAVE) + 1}/${Math.ceil(batches.length / WAVE)}`)
  const r = await parallel(chunk.map(b => () =>
    agent(prompt(b), { label: `solve:${b.n}`, phase: 'Solve' }).then(txt => ({ raw: txt || '' }))
  ))
  all.push(...r.filter(Boolean))
}
const rows = []
for (const res of all) for (const line of res.raw.split('\n')) {
  const t = line.trim(); if (!t || !t.includes('|')) continue
  const p = t.split('|').map(s => s.trim())
  const idTok = p.find(x => /^[0-9a-f]{8}-[0-9a-f]{4}-/.test(x)); if (!idTok) continue
  const idx = p.indexOf(idTok)
  const ans = (p[idx + 1] || '').toUpperCase().replace(/[^ABCDE]/g, '').slice(0, 1)
  rows.push({ id: idTok, ans, conf: parseFloat(p[idx + 2]) || 0 })
}
log(`DONE: ${rows.length} solved`)
return { parsed: rows.length, rows }
