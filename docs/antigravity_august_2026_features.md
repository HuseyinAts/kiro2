# Google Antigravity 2.0 (Gemini Ultra) - Ağustos 2026 Özellikleri ve Proje Kuralları

Bu belge, Google Antigravity 2.0'ın Ağustos 2026 resmi dokümantasyonundan, KIRO2 proje kural setlerinden (`CLAUDE.md`, `AGENTS.md`) ve sisteme entegre tüm yeteneklerden derlenmiş, eksiksiz bir referans dosyasıdır.

---

## 1. Antigravity 2.0 (Bağımsız Masaüstü Orkestrasyon Uygulaması)
IDE'ye bağımlı kalmadan ajanları masaüstünde otonom olarak çalıştıran ve izleyen Electron tabanlı masaüstü mimarisi.

### Sol Kenar Çubuğu (Left-hand Sidebar)
- **New Conversation:** Ajanla yeni bir sohbet seansı başlatma.
- **Projects:** Farklı çalışma alanları (workspace) veya repolar arası geçiş ve yönetim.
- **Scheduled Tasks:** Arka planda çalışan tekrarlı görevleri (cron) ve tek seferlik zamanlayıcıları (timers) tanımlama, izleme ve çalıştırma.
- **Skills & Customizations:** Aktif yetenekler (skills), kurallar (rules), eklentiler (plugins) ve MCP sunucularını görüntüleme/yönetme.
- **Settings:** Uygulama tercihleri, model seçimi ve izinlerin yapılandırılması.

### Chat Canvas (Evrensel Sohbet Ekranı)
- İşletim sistemine hükmedebilen devasa iletişim ve yönetim paneli.
- **Medya Yükleme (Drag & Drop):** Sohbet arayüzüne doğrudan fotoğraf, PDF veya belge sürükleyip bırakarak vizyon (Görüntü İşleme) modelini anında tetikleme.
- **Bağlam Yönetimi:** Yüklenen medyaların ve dosyaların mevcut mesaj için bağlam (context) olarak otomatik dahil edilmesi.

---

## 2. İleri Düzey Modeller ve Çoklu-Ajan (Multi-Agent) Mimarisi
- **Alt-Ajanlar (Subagents):** Ana ajanın, karmaşık görevleri parçalara ayırarak arka planda birden fazla uzman "alt-ajan" (Örn: codebase araştırmacısı) başlatıp paralel çalıştırma yeteneği.
- **Arka Plan Görev Yönetimi:** Uzun süren scriptler (örn: `npm install`, `docker build`) çalışırken ajanın bloklanmaması; görevi arka plana atıp cevap vermeye devam edebilmesi.
- **Gelişmiş Model Seçenekleri:** İhtiyaca göre dinamik model geçişi (Gemini Pro, Gemini Flash, Gemini Next).

---

## 3. Bağlam (Context) ve Atıf Yönetimi (@ ve /)

### Güçlendirilmiş `@` Mentions
- Sadece dosyaları değil; tüm klasörleri, geçmiş sohbetleri (Conversation ID), arka plan terminal seanslarını, kuralları ve MCP araçlarını doğrudan sohbete context olarak ekleyebilme.

### İşlevsel `/` Slash Komutları
- `/goal`: Ajanın hedefe ulaşana kadar pes etmeden, saatlerce otonom çalışmasını emreden mod.
- `/plan`: Kodlamadan önce adım adım mimari plan çıkartıp onayınıza sunma.
- `/schedule`: Ajanın belirli bir rutinde veya zamanda kendi kendini tetiklemesi.
- `/grill-me`: Kararsız kalınan mimari süreçlerde ajanın kullanıcıya çapraz sorgu yaparak yönlendirmesi.
- `/teamwork-preview`: Büyük projelerde görevleri kendi aralarında bölüşüp paralel çalışan otonom bir "Ajan Takımı" (Team of Autonomous Agents) başlatma.
- `/learn`: Bir konfigürasyonu veya karmaşık bir kurulumu birlikte çözüldüğünde, ajanın bu çözümü öğrenip gelecekteki görevler için kalıcı olarak belleğine kazıması.

---

## 4. Antigravity IDE (Editör İçi Yapay Zeka Mimarisi)
VS Code üzerine inşa edilmiş, agentic workflow'ları doğrudan kodlama ortamına entegre eden sistem.

### A. Pasif Mod (Antigravity Tab / Autocomplete)
- **Context-Aware Suggestions:** Çevredeki koda, açık sekmelere, terminal çıktılarına ve panoya dayalı ekleme, silme, düzenleme ve içe aktarma önerileri.
- **Autocomplete & Supercomplete:** İmleçte kod önerme ve daha büyük diff'leri (silmeler dahil) yüzen pencerelerde (floating windows) sunma.
- **Tab to Jump:** Bir sonraki navigasyon noktasını tahmin edip `Tab` ile atlama.
- **Tab to Import:** Yeni bir bağımlılık kullanıldığında gerekli import'ları dosyanın en üstüne otomatik ekleme.

### B. Instruktif Mod (Cmd+I / Ctrl+I)
- **Targeted Edits:** Seçili kod bloğunu refactor etme, açıklama veya değiştirme (Sadece seçili alanı düzenler).
- **Code Generation:** Seçim yapmadan imleç konumunda yepyeni kod üretme.
- **Localized Docs:** Hızlıca yorum, docstring veya lokalize dokümantasyon ekleme.

### C. İşbirlikçi Mod (Sidebar Chat & Agent)
- **Sidebar Chat:** Sorular sormak, özellik planlamak veya kodu tartışmak için ana panel.
- **Agent Mode:** Dosyaları okuyan/yazan, terminal komutları çalıştıran, web'de arama yapan çok adımlı işbirlikçi.
- **Planning Mode:** Ajanın adım adım planını yürütmeden önce inceleme ve düzeltme.

### Editör İçi Entegrasyonlar
- **Inline Code Lenses:** Sınıfların ve fonksiyonların üzerinde beliren "Refactor", "Test Yaz", "Açıkla" gibi tıklanabilir eylem butonları.
- **Visual Diff Overlays:** Editör içinde kırmızı/yeşil diff göstergeleri ile önerilen düzenlemeleri satır içi inceleme.
- **Diagnostic Auto-Fix:** Linter uyarıları veya derleyici hatalarından doğrudan ajanı tetikleyerek hatayı otonom onarma.
- **Workspace-Scoped Customizations:** `<project-root>/.agents/` klasöründeki projeye özel kuralları, yetenekleri ve eklentileri otomatik tanıma.

---

## 5. Model Context Protocol (MCP) ve Geliştirici Modülleri
- **MCP Sunucuları (`/docs/mcp`):** Harici araçları, veritabanlarını veya şirket içi API'leri ajana bağlayan standart protokol.
- **Yetenekler (Skills - `/docs/skills`):** Ajanın spesifik bir görevi nasıl yapacağını anlatan paylaşımlı yetenek setleri.
- **Kurallar (Rules - `/docs/rules`):** Proje veya sistem genelinde zorunlu tutulan davranış setleri.
- **Hooks (`/docs/hooks`):** Git pre-commit veya build süreçlerine ajanın doğrudan kanca atarak standartları denetlemesi.
- **Sidecars (`/docs/sidecars`):** IDE veya uygulamanın yanında koşan yardımcı analiz süreçleri.
- **Browser Automation & Testing (`/docs/browser`):** Ajanın arka planda (headless) veya görünür olarak web testleri yapması.
- **Plugins (Eklentiler - `/docs/plugins`):** `chrome-devtools-plugin`, `google-antigravity-sdk`, `modern-web-guidance-plugin`, `science` (AlphaFold, PubMed, PyMOL vb. devasa bilimsel veritabanı entegrasyonları).

---

## 6. HTML Auxiliary Pane (Yardımcı Panel)
Antigravity 2.0 masaüstü uygulamasında sağ tarafta/ayrı sekmede açılan kontrol paneli:
- **Subagents:** Alt ajanların ne düşündüğünü ve ne yaptığını anlık izleme.
- **Background Tasks:** Arka planda dönen cron veya scriptlerin logları.
- **Artifacts:** Ajanın ürettiği markdown tabanlı uzun raporlar, şemalar (Mermaid.js), carousel slaytlar ve "scratch" scriptlerinin tutulduğu dizin.
- **Files Changed:** Değişen dosyaların anlık izlendiği (diff) sekmesi.
- **Terminals:** Ajanın açtığı tüm terminal seanslarının canlı görünümü.

---

## 7. Güvenlik, Gizlilik, İzinler ve İnceleme Modları

### Global Ayarlar
- **Tool Execution Policy:** Terminal komutları için `always-proceed`, `request-review`, `strict`, `proceed-in-sandbox`.
- **Terminal Sandbox:** Ajan komutlarını ana makineye zarar vermemesi için kısıtlı bir sanal alanda koşturma.
- **Non-Workspace File Access:** Çalışma dizini dışındaki dosyalara erişim (`allow`, `ask`, `deny`).
- **Internet Access Policy:** Ağ istekleri ve web araması izinleri (`allow`, `ask`, `deny`).
- **Command Allowlist / Denylist:** Her zaman serbest (Örn: `npm run dev`) veya tamamen yasak (Örn: `rm -rf`) komut listeleri.
- **Browser Allowlist:** Ajanın otomasyon için girebileceği URL'lerin kısıtlanması.
- **Artifact Review Mode:** Rapor veya kod sunumlarında davranış kipi (`always-proceed`, `agent-decides`, `asks-for-review`).
- **App Settings:** Bilgisayarı uyanık tutma (Keep computer awake) ve arka planda çalışma (Run in background).

### Proje Bazlı Ayarlar (Overrides)
Proje kökündeki `.agents/` konfigürasyonları, global ayarları ezerek projeye özel kum havuzu (sandbox), internet ve dosya erişim politikaları atar.

---

## 8. Antigravity Python SDK (`google-antigravity`)
- **`Agent(config)` Async Context Manager:** `LocalAgentConfig` ve `CapabilitiesConfig` ile Python kodu içinden programatik ajan oluşturma.
- **Streaming Thoughts & Tool Calls:** Ajanın arka plandaki akıl yürütme sürecini (`response.thoughts`) ve çalıştırdığı araçları (`response.tool_calls`) asenkron olarak anlık loglama/yakalama.
- **Interactive Loop (`run_interactive_loop`):** Terminal tabanlı özel ajan sohbet döngüsü oluşturma.

---

## 9. Modern Web UI Standartları (Design Aesthetics)
- "Sıradan" (generic red/blue) tasarımlar kesinlikle reddedilir.
- HSL renk paletleri, Glassmorphism, koyu mod (Dark Mode) destekleri zorunludur.
- Mikro-animasyonlar, pürüzsüz geçişler ve Inter/Roboto gibi modern tipografiler kullanılarak kullanıcının "WOW" diyeceği **Premium** seviye dinamik tasarımlar oluşturulmalıdır.
- Kullanıcı özellikle istemedikçe TailwindCSS yerine Vanilla CSS (index.css) tercih edilmelidir.

---

## 10. KIRO2 Proje Kuralları (CLAUDE.md ve AGENTS.md)

### A. Karpathy Davranış Prensipleri
- **Önce Düşün, Sonra Kodla:** Varsayım yapma. `grep` ile doğrula. Ezbere kod yazma.
- **Önce Sadelik (KISS/YAGNI):** İstenmeyen esneklikler, gereksiz soyutlamalar ekleme.
- **Cerrahi Müdahale:** İlgisiz kısımları formatlama, refactor etme.
- **Hedef Odaklı Yürütme (TDD):** Hata çözmeden önce fail eden test yaz, sonra kodu düzelt, testin PASS olduğunu kanıtla.

### B. Kesin (Hard) Kurallar
- Doğru veritabanı Host PostgreSQL 18'dir (port 5434). `kiro2_postgres` container'ı kullanılmamalıdır.
- Pipeline-Fix işlemlerinde **Çift Sinyal (Key Match + Text Similarity)** zorunludur. Gemini `q_no` çıktılarına tek başına güvenilemez.
- Türkçe metin normalizasyonunda standart: Önce `NFC Unicode Normalization`, ardından Türkçe mapping (`İ→i`, `I→ı`), en son `lowercase`.

### C. Debugging ve İnceleme (Audit) Protokolleri
- **Kök Neden Analizi:** Bug çözümü öncesi `.claude/rules/debugging-first.md` formatında tablo sunulması zorunludur.
- **Progressive Checkpoint:** Sistem çökme riskine karşı her commit sonrası `.claude/sessions/latest.md` dosyası güncellenmelidir.
- **Mega Audit Lock (S197):** 10'dan fazla dokümanı kapsayan taramalarda (Mega Audit), geçmiş P0/P1 backlog'unun en az %80'inin kapanmış olması veya "phantom verify pass" yapılması zorunludur.

### D. Arama (Ripgrep) ve Git Kuralları
- Root klasörde (`C:\Users\husey\kiro2`) doğrudan `rg` çalıştırmak yasaktır (Timeout riski). Aramalar hedefe (`backend/app/`, `frontend/`) yönelik yapılmalıdır.
- 50MB üzerindeki (`*.jsonl`, `*.bin`, `*.db`) dosyalar commit edilmemeli, `git-lfs` veya `.gitignore` ile yönetilmelidir.

### E. Görev Yönlendirme (Routing)
- Frontend UI, basit testler ve CSS görevleri: **Codex**.
- Türk NLP'si, mimari kararlar, d-dataset pipeline'ları, refactoring ve güvenlik denetimleri: **Claude (Antigravity)**.

---
*Bu doküman, Ağustos 2026 itibariyle Google Antigravity sistemine entegre edilen resmi özellikler ile KIRO2 projesinin zorunlu best practice kurallarının tam bir dökümüdür.*
