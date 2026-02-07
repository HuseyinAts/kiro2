# 🤖 Gemini MCP Kullanım Kılavuzu

**Durum:** ✅ Gemini MCP Çalışıyor!  
**Model:** Gemini Experimental 1206

---

## ✅ Gemini MCP Durumu

```
✅ MCP Sunucusu: Yapılandırıldı
✅ Gemini Model: Yüklendi (Gemini Experimental 1206)
✅ API Key: Tanımlı
✅ Araçlar: 4 adet hazır
```

---

## 🚀 Kullanım Yöntemleri

### Yöntem 1: Python Script ile Doğrudan Kullanım (ÖNERİLEN)

Kiro IDE'de "Agents" bölümü olmadığı için, Gemini'yi doğrudan Python scripti ile kullanabilirsiniz.

#### Adım 1: Test Scriptini Çalıştırın

```bash
py test_gemini_direct.py
```

#### Adım 2: Mod Seçin

```
Gemini MCP Kullanım Seçenekleri:
1. Test Modu (otomatik testler)
2. İnteraktif Mod (sohbet)

Seçiminiz (1 veya 2): 2
```

#### Adım 3: Gemini ile Sohbet Edin!

```
💬 Siz: Merhaba Gemini! Kendini tanıt.

🤖 Gemini düşünüyor...

🤖 Gemini Yanıtı:

Merhaba! Ben Gemini, Google'ın geliştirdiği büyük bir dil modeliyim...
```

---

### Yöntem 2: Kiro Chat'te MCP Araçlarını Kullanma

Eğer Kiro IDE'de chat özelliği varsa, MCP araçları otomatik olarak kullanılabilir olmalı.

#### Kiro Chat'i Açın

```
1. Kiro IDE'de chat panelini açın
2. Normal şekilde soru sorun
3. Kiro otomatik olarak Gemini MCP araçlarını kullanacak
```

#### Örnek Sorular

```
"Bu Python kodunu analiz et ve optimize et"
"Design.md dosyasını incele ve iyileştirme önerileri sun"
"LGS matematik sorusu üret"
```

---

### Yöntem 3: Python Kodunda Doğrudan Kullanım

Kendi Python scriptlerinizde Gemini'yi kullanabilirsiniz:

```python
import asyncio
from backend.mcp_servers.gemini_reasoning_mcp import gemini_reasoning_engine

async def main():
    result = await gemini_reasoning_engine(
        prompt="Python'da async/await nasıl çalışır?",
        thinking_mode=True
    )
    print(result)

asyncio.run(main())
```

---

## 🎯 Gemini MCP Araçları

### 1. gemini_reasoning_engine

**Kullanım:** Genel amaçlı akıl yürütme ve analiz

```python
from backend.mcp_servers.gemini_reasoning_mcp import gemini_reasoning_engine

result = await gemini_reasoning_engine(
    prompt="Bu sistemi nasıl ölçeklendirebilirim?",
    context="FastAPI backend, PostgreSQL, Redis",
    thinking_mode=True
)
```

**Parametreler:**
- `prompt` (str): Soru veya görev
- `context` (str, opsiyonel): Ek bağlam
- `thinking_mode` (bool): Detaylı akıl yürütme (varsayılan: True)

---

### 2. gemini_code_review

**Kullanım:** Kod incelemesi ve optimizasyon

```python
from backend.mcp_servers.gemini_reasoning_mcp import gemini_code_review

code = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total
"""

result = await gemini_code_review(
    code=code,
    language="python"
)
```

**Parametreler:**
- `code` (str): İncelenecek kod
- `language` (str): Programlama dili (varsayılan: "python")

---

### 3. gemini_design_analysis

**Kullanım:** Sistem tasarım dokümanı analizi

```python
from backend.mcp_servers.gemini_reasoning_mcp import gemini_design_analysis

with open("design.md", "r", encoding="utf-8") as f:
    design_doc = f.read()

result = await gemini_design_analysis(design_doc=design_doc)
```

**Parametreler:**
- `design_doc` (str): Design.md dosyasının içeriği

---

### 4. gemini_requirements_analysis

**Kullanım:** Gereksinim dokümanı analizi

```python
from backend.mcp_servers.gemini_reasoning_mcp import gemini_requirements_analysis

with open("requirements.md", "r", encoding="utf-8") as f:
    requirements_doc = f.read()

result = await gemini_requirements_analysis(requirements_doc=requirements_doc)
```

**Parametreler:**
- `requirements_doc` (str): Requirements.md dosyasının içeriği

---

## 💡 Pratik Örnekler

### Örnek 1: Hızlı Soru-Cevap

```bash
# Terminal'de çalıştırın
py test_gemini_direct.py

# Seçim: 2 (İnteraktif Mod)

💬 Siz: Python'da decorator nedir?

🤖 Gemini: [Detaylı açıklama]
```

---

### Örnek 2: Kod İncelemesi

```python
# kod_incele.py
import asyncio
from backend.mcp_servers.gemini_reasoning_mcp import gemini_code_review

async def main():
    kod = """
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)
    """
    
    sonuc = await gemini_code_review(kod, "python")
    print(sonuc)

asyncio.run(main())
```

```bash
py kod_incele.py
```

---

### Örnek 3: Dosya Analizi

```python
# dosya_analiz.py
import asyncio
from backend.mcp_servers.gemini_reasoning_mcp import gemini_design_analysis

async def main():
    with open("design.md", "r", encoding="utf-8") as f:
        icerik = f.read()
    
    sonuc = await gemini_design_analysis(icerik)
    print(sonuc)

asyncio.run(main())
`ın.
ullanzde kscriptlerinidi Python  kenın veyai çalıştır scriptinestiçin tnız 
Sorularıır! 🚀**
 hazCP kullanımaemini M
**G`

---
``: Merhaba!
💬 Sizet et!
sohbemini ile  G 2

# 3.
Seçiminiz:mod seç (2) İnteraktif 
# 2..py
ct_dire test_geminir
pyini çalıştıst scriptash
# 1. Teıç

```b Başlangzlı-

## ✅ Hı

--` dosyasındaKey:** `.envI 
- **APmcp.json`ttings\iro\sey\.khuse`C:\Users\:** masıandırP Yapıl**MC`
- pyning_mcp.asogemini_re_servers/`backend/mcpucu:** P Sun- **MCct.py`
ni_dire* `test_gemii:**Test Scriptr

- *akla Ek Kayn

## 📚

---)
```ompt_engine(prngi_reasonit geminult = awai
res"""
: Orta
viyesi
Öğrenci selar
n hataaygır
4. Yrnekle3. Ömüller
ar
2. Forl kavraml
1. Teme için:saları'u 'Newton Yaizik konus"
YKS Fompt = ""ython
pr
```pi
tımı Üretimonu Anla
### Kt)
```
prompgine(ing_eneasont gemini_r= awai

result 
"""r.yolu öneş öğrenme tirilmiiselleş/100

Kiş: 55100
- Fen0/kçe: 8
- Tür 65/100atematik::
- M etarını analizçln test sonuniu öğrenci
B= """hon
prompt 
```pyts Analizi
 Performanenci Öğr

###el Kullanımçin ÖzProjesi İknofest ## 🎓 Te

---
`
)
``tif
ng mode ak  # Thinking_mode=Truehinki,
    tr"dierlenimariyi değiz: Bu mtaylı anal prompt="De
   ine(asoning_enggemini_re await sult =on
re``pythçin

`Analiz İ## Detaylı 
```

#at
)kapde'u  mongkihin=False  # Tg_modehinkin    t",
dir?ython neevap: PKısa c prompt="
   g_engine(asoninreni_= await gemit on
resul
```pytht İçin
# Hızlı Yanı

##rılaormans İpuç
## 📊 Perf-


--mcp
```fasti ativeale-genernstall googm pip in
py -e kurusiks"

# Ektmcping "fasStrt-Select | -m pip lisi"
py -generativeagoogleng " Select-Strip list |y -m pi edin
polleri kontraketrekli pbash
# Gezüm:**
```or

**Çöşmıy Script Çalı 4:### Sorun

---

com/
```udio.google.ps://aisthttntrol edin: 'da koAI StudioGoogle min olun
# ndan erli olduğu'in geçePI key A`bash
#**
``
**Çözüm:
"ErrorAPI run 3: "So# 
##
---

py
```ct.mini_dire
py test_ge"".:PYTHONPATH=nvrlayın
$eTHONPATH ayabash
# PY
```:**üm**Çözfound"

dule not "Mon 2: # Soru##
---

``
A
`UvWVTHDrHU41NzWnTLs7KSM64qj3DIeEY=AIzaSyBGLE_API_Kl edin
GOOsını kontro.env dosya``bash
# züm:**
`"

**Çöt foundnoAPI_KEY : "GOOGLE_# Sorun 1e

##orun Giderm

## 🔧 S---`

``ret.py
_uash
py soru`

```b)
``(main()asyncio.runc)

print(sonu
    True)_mode=, thinking(promptning_engine_reasoawait gemini=    sonuc    
 ""
 ası
    "ıklam Çözüm açap
    4.ğru cev
    3. Do(A, B, C, D) 2. 4 şık 
   itnu me   1. Sor
 n:u içi
    Her sor.
     soru üret seviyesindet LGSçin 3 adeÜçgenler' i konusu 'f Matematiksını8.    "
 t = ""mp:
    prodef main()ync 
ase
g_enginasoninmini_rep import gesoning_mcini_rea_servers.gemckend.mcpio
from basynct apor.py
imsoru_uretpython
# 

``` Projesi) (Teknofestetimi LGS Soru Ür### Örnek 4:--



-liz.py
```a_ana dosy`bash
py``

``