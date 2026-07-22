// KIRO2 — kiro-api.js: openapi.yaml sözleşmesinin ÇALIŞAN mock uygulaması (prototip backend'i).
// Üretimde bu dosyanın yerini gerçek fetch alır (design_handoff_kiro2/api-client.ts mock↔live);
// ekranlar ve konsol aynı çağrı imzasıyla çalışmaya devam eder.
// Sunucu-otoriter kanon: `dogru`/çözüm YALNIZ answer yanıtında iner; CAT seçimi + θ sunucuda;
// hata zarfı { error: { code, message } }; "eksik" kelimesi hiçbir yanıtta yok.

async function db() {
  if (window.__KIRO) return window.__KIRO;
  try { const K = await import('./kiro-data.js'); return K.default || K; } catch (e) { return null; }
}
const gecikme = () => new Promise((r) => setTimeout(r, 120 + Math.random() * 230));
const err = (code, message) => ({ error: { code, message } });
const ST_KEY = 'kiro2-api-state';
function st() { try { return JSON.parse(localStorage.getItem(ST_KEY)) || {}; } catch (e) { return {}; } }
function setSt(patch) { const s = Object.assign(st(), patch); try { localStorage.setItem(ST_KEY, JSON.stringify(s)); } catch (e) {} return s; }

export async function kiroApi(method, path, body) {
  const t0 = performance.now();
  await gecikme();
  const K = await db();
  const done = (status, json) => ({ status, ms: Math.round(performance.now() - t0), json });
  if (!K) return done(503, err('veri_yok', 'Veri katmanı yüklenemedi — sorun sende değil, çalışman güvende.'));
  const p = path.split('?')[0].split('/').filter(Boolean);
  const m = method.toUpperCase();
  const s = st();

  try {
    // ---- Öğrenci / genel ----
    if (m === 'GET' && path === '/me') return done(200, Object.assign({}, K.persona, { plan: s.plan || 'free', seri: s.seri || K.persona.seri }));
    if (m === 'GET' && path === '/engine') return done(200, K.engine);
    if (m === 'GET' && path === '/level') { const xp = s.xp || K.persona.xp; return done(200, K.seviyeBilgi ? K.seviyeBilgi(xp) : { xp }); }
    if (m === 'POST' && path === '/me/mood') {
      if (!body || !body.deger) return done(400, err('deger_gerekli', 'deger alanı zorunlu (bitkin|gergin|idare|iyi|harika).'));
      setSt({ mood: body.deger }); return done(200, { ok: true, not: 'Veliye asla gösterilmez.' });
    }
    // ---- Dersler / içerik ----
    if (m === 'GET' && path === '/subjects') return done(200, K.subjects);
    if (m === 'GET' && path === '/topics') return done(200, K.topics);
    if (m === 'GET' && p[0] === 'curriculum' && p[1]) {
      const c = K.curriculum && K.curriculum[p[1]];
      return c ? done(200, c) : done(404, err('ders_yok', "Bu ders için ünite ağacı henüz yayında değil."));
    }
    if (m === 'GET' && p[0] === 'topics' && p[2] === 'atoms') {
      const konu = decodeURIComponent(p[1]);
      const a = K.atomlarByKonu ? K.atomlarByKonu(konu) : null;
      return a ? done(200, a) : done(404, err('atom_yok', 'Bu konu için atom kırılımı yok — konu düzeyinde çalışılır.'));
    }
    // ---- Çekirdek döngü ----
    if (m === 'GET' && path === '/review/due') {
      const graded = s.graded || {};
      return done(200, K.reviewQueue.filter((r) => r.dueIn === 0 && !graded[r.konu]).map((r) => ({ konu: r.konu, ders: r.ders, kart: r.kart })));
    }
    if (m === 'POST' && p[0] === 'review' && p[2] === 'grade') {
      const konu = decodeURIComponent(p[1]);
      const derece = body && body.derece;
      if (![1, 2, 3, 4].includes(derece)) return done(400, err('derece_gecersiz', 'derece 1-4 olmalı.'));
      const graded = Object.assign({}, s.graded, {}); graded[konu] = derece; setSt({ graded });
      const aralik = ['', '10 dk', '1 gün', '3 gün', '7 gün'][derece];
      return done(200, { konu, sonrakiAralik: aralik, not: 'Aralık FSRS zamanlayıcısından (sunucu).' });
    }
    if (m === 'POST' && p[0] === 'questions' && p[2] === 'answer') {
      const id = decodeURIComponent(p[1]);
      const q = (K.questionBank || []).find((x) => x.id === id) || (K.questionBank || [])[0];
      if (!q) return done(404, err('soru_yok', 'Soru bulunamadı.'));
      if (!body || typeof body.secim === 'undefined') return done(400, err('secim_gerekli', 'secim zorunlu (null = Emin değilim).'));
      const dogruMu = body.secim === q.dogru;
      setSt({ xp: (s.xp || K.persona.xp) + (dogruMu ? 15 : 5) });
      return done(200, { dogruMu, dogru: q.dogru, cozum: q.cozum, neden: q.neden, xp: dogruMu ? 15 : 5, not: 'dogru/çözüm YALNIZ bu yanıtla iner (kanon).' });
    }
    if (m === 'POST' && path === '/cat/next') {
      const theta = (body && typeof body.theta === 'number') ? body.theta : 0;
      const yeniTheta = theta + ((body && body.sonDogru) ? 0.18 : -0.15);
      const havuz = (K.catBankMat || []).slice().sort((a, b) => Math.abs(a.b - yeniTheta) - Math.abs(b.b - yeniTheta));
      const sec = havuz[0];
      if (!sec) return done(404, err('havuz_bos', 'Uygun madde kalmadı.'));
      const item = { id: sec.id || sec.konu, konu: sec.konu, soru: sec.soru, secenekler: sec.secenekler, b: sec.b, a: sec.a };
      return done(200, { theta: Math.round(yeniTheta * 100) / 100, se: 0.42, item, not: "Madde seçimi + θ SUNUCUDA; 'dogru' bu yanıtta YOK (kanon)." });
    }
    if (m === 'GET' && path === '/exams/last') { const e2 = K.lastExam; return done(200, { ad: e2.ad, tarih: e2.tarih, tytNet: e2.tytNet, aytNet: e2.aytNet, toplam: e2.toplam, tahminiSiralama: e2.tahminiSiralama }); }
    if (m === 'POST' && path === '/streak/checkin') {
      const bugun = new Date().toISOString().slice(0, 10);
      if (s.lastCheckin === bugun) return done(200, { seri: s.seri || K.persona.seri, zatenVar: true });
      const seri = (s.seri || K.persona.seri) + 1; setSt({ seri, lastCheckin: bugun });
      return done(200, { seri });
    }
    // ---- Roller ----
    if (m === 'GET' && path === '/assignments') {
      const prog = s.odevProg || {};
      return done(200, (K.odevler || []).map((o) => Object.assign({}, o, prog[o.id] ? { cozulen: prog[o.id] } : {})));
    }
    if (m === 'POST' && p[0] === 'assignments' && p[2] === 'progress') {
      const id = decodeURIComponent(p[1]);
      const odevProg = Object.assign({}, s.odevProg); odevProg[id] = (body && body.cozulen) || 0; setSt({ odevProg });
      return done(200, { id, cozulen: odevProg[id], durumDili: 'geciken = "bekliyor" — "eksik" yok (kanon).' });
    }
    if (m === 'GET' && p[0] === 'teacher' && p[1] === 'classes') return done(200, [{ id: 'c1', ad: '12-A', katilimKodu: '482913', ogrenci: (K.sinifRoster || []).length }]);
    if (m === 'POST' && p[0] === 'teacher' && p[1] === 'classes') {
      if (!body || !body.ad) return done(400, err('ad_gerekli', 'Sınıf adı zorunlu.'));
      return done(201, { id: 'c' + Date.now(), ad: body.ad, katilimKodu: String(100000 + Math.floor(Math.random() * 899999)), varsayilanlar: 'sıralama yayınlanmaz · risk bayrağı öğrenciye inmez (sunucu yazar)' });
    }
    if (m === 'POST' && path === '/me/class/join') {
      if (!body || body.kod !== '482913') return done(404, err('kod_gecersiz', 'Kod bulunamadı — öğretmenden yeni kod isteyebilirsin.'));
      return done(200, { sinif: { id: 'c1', ad: '12-A' } });
    }
    // ---- Bildirim / fatura / auth ----
    if (m === 'GET' && path === '/notifications') {
      const due = K.reviewQueue.filter((r) => r.dueIn === 0);
      return done(200, [
        { tur: 'fsrs', baslik: 'Tekrar zamanı geldi', govde: due.length + ' konu bekliyor — 15 dk yeter.' },
        { tur: 'deneme', baslik: 'Deneme analizin hazır', govde: K.lastExam.ad },
      ]);
    }
    if (m === 'GET' && path === '/billing/plans') return done(200, { aylik: { tl: 199 }, yillik: { tlAy: 124, tl: 1490, indirim: '%38' }, deneme: { gun: 7, not: 'Bugün ödeme alınmaz; sessizce ücret alınmaz.' } });
    if (m === 'POST' && path === '/auth/login') {
      if (!body || !body.eposta) return done(400, err('eposta_gerekli', 'E-posta zorunlu.'));
      return done(200, { token: 'mock.jwt.' + btoa(body.eposta).slice(0, 12), yenileme: 'mock.refresh', not: 'Gerçek JWT ADR-001 ile sunucuda.' });
    }
    return done(404, err('uc_yok', m + ' ' + path + ' bu mock\'ta tanımlı değil — openapi.yaml otoriter.'));
  } catch (e) {
    return done(500, err('mock_hata', String(e && e.message || e)));
  }
}

export function apiDurumSifirla() { try { localStorage.removeItem(ST_KEY); } catch (e) {} }
export default kiroApi;
