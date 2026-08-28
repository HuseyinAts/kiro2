"""KVKK Md.10 — Aydınlatma metni (veri sorumlusunun aydınlatma yükümlülüğü).

Rıza (consent) alınmadan ÖNCE ilgili kişiye gösterilmesi gereken metin.
Public (auth gerektirmez) — disclosure, rıza öncesi okunabilmeli.

`version` alanı, consent akışındaki `privacy_policy_version` ile eşleşir; kullanıcı
hangi metin sürümüne rıza verdiğinin izini bu sürümle tutar.

B2B bağlamı: okul/kurum = veri sorumlusu, KIRO2 = veri işleyen (DPA ile).
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/kvkk/notice", tags=["KVKK Notice"])

# Metin güncellenince SÜRÜM artırılmalı (consent privacy_policy_version ile hizalı).
NOTICE_VERSION = "v1"
NOTICE_EFFECTIVE_DATE = "2026-07-04"

AYDINLATMA_METNI = """\
KİŞİSEL VERİLERİN İŞLENMESİNE İLİŞKİN AYDINLATMA METNİ

6698 sayılı Kişisel Verilerin Korunması Kanunu ("KVKK") m.10 kapsamında,
kişisel verileriniz aşağıda açıklanan çerçevede işlenmektedir.

1) VERİ SORUMLUSU
KIRO2 platformu üzerinden hizmet aldığınız eğitim kurumu/okul, işlediğiniz
öğrenci ve kullanıcı verileri bakımından veri sorumlusudur. KIRO2, kurum adına
ve talimatları doğrultusunda veri işleyen sıfatıyla hareket eder (kurum ile
imzalanan Veri İşleme Sözleşmesi/DPA kapsamında).

2) KİŞİSEL VERİLERİN İŞLENME AMAÇLARI
- Üyelik/hesap oluşturma ve kimlik doğrulama,
- Sınav hazırlık hizmetinin sunulması (soru bankası, deneme, ödev, ilerleme),
- Öğrenme analitiği ve kişiselleştirilmiş çalışma planı,
- Veli/öğretmen bilgilendirmesi ve raporlama,
- Hizmet güvenliği, hile önleme ve yasal yükümlülüklerin yerine getirilmesi.

3) İŞLENEN VERİ KATEGORİLERİ
Kimlik ve iletişim (ad, e-posta, kullanıcı adı), eğitim/performans verileri
(sınav yanıtları, ilerleme, kazanım), kullanım/işlem kayıtları ve — reşit
olmayan kullanıcılar için — veli/vasi iletişim bilgisi.

4) VERİLERİN AKTARILDIĞI TARAFLAR VE AMACI
Veriler; hizmetin sunulması için gerekli olduğu ölçüde bağlı olduğunuz eğitim
kurumuna, yetkili kamu kurum ve kuruluşlarına (yasal talep hâlinde) ve teknik
altyapı sağlayıcılarına (barındırma/işleme) aktarılabilir. Yurt dışına aktarım
yapılmamaktadır; yapılacak olması hâlinde KVKK m.9 şartları sağlanır.

5) TOPLAMA YÖNTEMİ VE HUKUKİ SEBEP
Veriler; platform üzerinden elektronik ortamda, açık rızanız ve/veya
sözleşmenin ifası, hukuki yükümlülük ve meşru menfaat hukuki sebeplerine
dayanılarak toplanır (KVKK m.5).

6) İLGİLİ KİŞİNİN HAKLARI (KVKK m.11)
Kişisel verilerinizle ilgili olarak; işlenip işlenmediğini öğrenme, bilgi
talep etme, işlenme amacını öğrenme, aktarıldığı tarafları bilme, eksik/yanlış
işlenmişse düzeltilmesini, şartları oluştuğunda silinmesini/yok edilmesini,
düzeltme/silme işlemlerinin aktarıldığı taraflara bildirilmesini, otomatik
sistemlerle analiz sonucu aleyhinize bir sonucun ortaya çıkmasına itiraz etme
ve zarara uğramanız hâlinde giderim talep etme haklarına sahipsiniz.

Bu hakları platform üzerinden; rıza yönetimi (/kvkk/consent), veri dışa
aktarma (/kvkk/privacy/export) ve veri silme (/kvkk/privacy/delete) işlevleri
ile veya bağlı olduğunuz kuruma başvurarak kullanabilirsiniz.
"""


class NoticeOut(BaseModel):
    version: str
    effective_date: str
    text: str


@router.get("", response_model=NoticeOut)
async def get_privacy_notice() -> NoticeOut:
    """Yürürlükteki aydınlatma metni + sürüm (public; rıza öncesi okunabilir)."""
    return NoticeOut(
        version=NOTICE_VERSION,
        effective_date=NOTICE_EFFECTIVE_DATE,
        text=AYDINLATMA_METNI,
    )


@router.get("/version")
async def get_notice_version() -> dict:
    """Güncel sürüm (consent privacy_policy_version ile eşleme için)."""
    return {"version": NOTICE_VERSION, "effective_date": NOTICE_EFFECTIVE_DATE}
