"""
Generate the double-blind-solve Workflow script from the readable pilot.

v2: rate-limit hardened. Önceki run 222/240 agent 429 yedi (pipeline ~16
eşzamanlı → server throttle). Düzeltme: küçük sıralı dalgalar (BATCH eşzamanlı),
429'da tek retry. L1 dersi: ≤6 eşzamanlı.

Usage: python generate_workflow.py [LIMIT] [BATCH]
  LIMIT: kaç soru (default 120)   BATCH: eşzamanlı zincir (default 4)

- Embeds ONLY blind data (id, subject, exam, question_text, options) — NO answer.
- Writes pool_pilot_answers.json (id -> correct_answer) for Phase-2.
"""

import json
import sys
from pathlib import Path

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 120
BATCH = int(sys.argv[2]) if len(sys.argv) > 2 else 4

HERE = Path(__file__).parent
readable = [
    json.loads(line)
    for line in (HERE / "pool_pilot_readable.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
    if line.strip()
][:LIMIT]

answers = {r["id"]: r["correct_answer"] for r in readable}
(HERE / "pool_pilot_answers.json").write_text(
    json.dumps(answers, ensure_ascii=False), encoding="utf-8"
)

blind = [
    {
        "id": r["id"],
        "subject": r["subject_area"],
        "exam": r["exam_type"],
        "q": r["question_text"],
        "options": r["options"],
    }
    for r in readable
]
QUESTIONS_JS = json.dumps(blind, ensure_ascii=False)

script = (
    (
        """export const meta = {
  name: 'pool-growth-double-blind-pilot',
  description: 'unverified+pending pilot sorularini DB cevabi VERMEDEN iki bagimsiz kor-solve ile coz (rate-limit hardened, kucuk dalgalar)',
  phases: [
    { title: 'DoubleBlind' },
  ],
}

const QUESTIONS = __QUESTIONS__
const BATCH = __BATCH__

function buildPrompt(qq, framing) {
  const opts = ['A','B','C','D','E']
    .map(k => qq.options[k] != null ? `${k}) ${qq.options[k]}` : null)
    .filter(Boolean).join('\\n')
  const persona = framing === 'A'
    ? 'Sen deneyimli bir YKS hazirlik ogretmenisin. Soruyu dikkatle oku ve dogru sikki bul.'
    : 'Bagimsiz bir cozucusun. Adim adim akil yurut, her secenegi degerlendir, sonra karar ver.'
  return [
    persona,
    '',
    'ONEMLI: Sana cevap anahtari VERILMEDI. Soruyu kendi bilginle coz.',
    'Eger soru OKUNAMIYOR / bozuk-OCR / figur-bagimli (sekil/grafik gerekiyor ama yok) / coklu-soru karisik / coselemez ise SOLVABLE: no yaz.',
    '',
    `Ders: ${qq.subject || '?'} | Sinav: ${qq.exam || '?'}`,
    `Soru: ${qq.q}`,
    '',
    'Secenekler:',
    opts,
    '',
    'SADECE su tek satir formatinda yanit ver (baska hicbir sey yazma):',
    'ANSWER: <A|B|C|D|E|NONE> | CONF: <0.0-1.0> | SOLVABLE: <yes|no>',
  ].join('\\n')
}

function parse(t) {
  const s = String(t || '')
  const a = s.match(/ANSWER:\\s*([A-E]|NONE)/i)
  const c = s.match(/CONF:\\s*(0?\\.\\d+|1(?:\\.0)?|0|1)/i)
  const v = s.match(/SOLVABLE:\\s*(yes|no)/i)
  return {
    letter: a ? a[1].toUpperCase() : 'PARSE_FAIL',
    conf: c ? parseFloat(c[1]) : null,
    solvable: v ? v[1].toLowerCase() === 'yes' : null,
  }
}

function isRateLimited(t) {
  const s = String(t || '')
  return /API Error|temporarily limiting|rate/i.test(s) && !/ANSWER:/i.test(s)
}

// One blind solve with a single retry if the response is a rate-limit error.
async function blindSolve(qq, framing) {
  let t = await agent(buildPrompt(qq, framing), {
    label: `${framing === 'A' ? 'b1' : 'b2'}:${qq.id.slice(0, 6)}`,
    phase: 'DoubleBlind',
  })
  if (isRateLimited(t)) {
    t = await agent(buildPrompt(qq, framing), {
      label: `${framing === 'A' ? 'b1' : 'b2'}r:${qq.id.slice(0, 6)}`,
      phase: 'DoubleBlind',
    })
  }
  return parse(t)
}

// Small sequential waves: max BATCH concurrent chains; each chain runs its two
// blinds sequentially. Natural agent latency paces requests under the 429 ceiling.
const out = []
for (let i = 0; i < QUESTIONS.length; i += BATCH) {
  const slice = QUESTIONS.slice(i, i + BATCH)
  const res = await parallel(
    slice.map((qq) => async () => {
      const b1 = await blindSolve(qq, 'A')
      const b2 = await blindSolve(qq, 'B')
      return { id: qq.id, subject: qq.subject, exam: qq.exam, b1, b2 }
    }),
  )
  for (const r of res) if (r) out.push(r)
  log(`dalga ${Math.floor(i / BATCH) + 1}: ${out.length}/${QUESTIONS.length} tamamlandi`)
}

const okCount = out.filter(r => r.b1.letter !== 'PARSE_FAIL' && r.b2.letter !== 'PARSE_FAIL').length
log(`iki-blind gecerli yanit: ${okCount}/${out.length}`)
return { total: QUESTIONS.length, completed: out.length, ok: okCount, results: out }
"""
    )
    .replace("__QUESTIONS__", QUESTIONS_JS)
    .replace("__BATCH__", str(BATCH))
)

(HERE / "dblind_workflow.mjs").write_text(script, encoding="utf-8")
print(
    f"LIMIT={LIMIT} BATCH={BATCH} | answers.json + dblind_workflow.mjs yazildi ({len(script)} char)"
)
