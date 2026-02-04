"""
Öğretmen paneli servisi
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from models import KullaniciRolu

from .sinav_motoru_service import sinav_motoru_servisi
from .user_service import kullanici_servisi


class OgretmenServisi:
    """Öğretmen paneli ve sınıf yönetimi servisi"""

    def __init__(self):
        # In-memory veri saklama
        self.sinif_ogrenci_iliskileri: Dict[
            str, List[str]
        ] = {}  # ogretmen_id -> ogrenci_id_listesi
        self.ogrenci_notlari: Dict[str, Dict] = {}  # ogrenci_id -> notlar
        self.sinif_raporlari: Dict[str, Dict] = {}  # rapor_id -> rapor_verisi
        self.ogretmen_bildirimleri: Dict[
            str, List[Dict]
        ] = {}  # ogretmen_id -> bildirimler

    async def ogretmen_dashboard_verisi(self, ogretmen_id: str) -> Dict[str, Any]:
        """Öğretmen dashboard için temel verileri getir"""
        try:
            # Öğretmen profilini getir
            ogretmen_profili = await kullanici_servisi.ogretmen_profili_getir(
                ogretmen_id
            )
            if not ogretmen_profili:
                raise ValueError("Öğretmen profili bulunamadı")

            # Öğrenci listesini getir
            ogrenci_listesi = await self.ogrenci_listesi_getir(ogretmen_id)

            # Genel istatistikleri hesapla
            toplam_ogrenci = len(ogrenci_listesi)
            aktif_sinavlar = 0
            ortalama_basari = 0.0

            if ogrenci_listesi:
                # Her öğrenci için son sınav performansını al
                toplam_net = 0
                sinav_sayisi = 0

                for ogrenci in ogrenci_listesi:
                    son_sinavlar = await sinav_motoru_servisi.ogrenci_sinavlari(
                        ogrenci.ogrenci_id
                    )
                    if son_sinavlar:
                        # Son sınavın sonucunu al
                        son_sinav = max(son_sinavlar, key=lambda x: x.olusturma_tarihi)
                        sonuc = await sinav_motoru_servisi.sonuc_getir(
                            son_sinav.sinav_id
                        )
                        if sonuc:
                            toplam_net += sonuc.net_sayisi
                            sinav_sayisi += 1

                if sinav_sayisi > 0:
                    ortalama_basari = toplam_net / sinav_sayisi

            # Son bildirimleri getir
            son_bildirimler = await self.bildirimler_getir(ogretmen_id, limit=5)

            return {
                "ogretmen_profili": ogretmen_profili,
                "genel_istatistikler": {
                    "toplam_ogrenci": toplam_ogrenci,
                    "aktif_sinavlar": aktif_sinavlar,
                    "ortalama_basari": round(ortalama_basari, 2),
                    "son_guncelleme": datetime.now(),
                },
                "ogrenci_listesi": ogrenci_listesi[:10],  # İlk 10 öğrenci
                "son_bildirimler": son_bildirimler,
            }

        except Exception as e:
            raise ValueError(f"Dashboard verisi alınamadı: {str(e)}")

    async def ogrenci_listesi_getir(self, ogretmen_id: str) -> List[Dict[str, Any]]:
        """Öğretmenin sorumlu olduğu öğrenci listesini getir"""
        try:
            # Öğretmen-öğrenci ilişkilerini kontrol et
            ogrenci_ids = self.sinif_ogrenci_iliskileri.get(ogretmen_id, [])

            # Eğer ilişki yoksa, demo veriler oluştur
            if not ogrenci_ids:
                await self._demo_ogrenci_iliskileri_olustur(ogretmen_id)
                ogrenci_ids = self.sinif_ogrenci_iliskileri.get(ogretmen_id, [])

            ogrenci_listesi = []

            for ogrenci_id in ogrenci_ids:
                # Öğrenci profilini getir
                ogrenci_profili = await kullanici_servisi.ogrenci_profili_getir(
                    ogrenci_id
                )
                if not ogrenci_profili:
                    continue

                # Kullanıcı bilgilerini getir
                kullanici = await kullanici_servisi.kullanici_getir(
                    ogrenci_profili.kullanici_id
                )
                if not kullanici:
                    continue

                # Son performans verilerini getir
                son_performans = await self._ogrenci_son_performans(ogrenci_id)

                ogrenci_verisi = {
                    "ogrenci_id": ogrenci_id,
                    "ad_soyad": kullanici.ad_soyad,
                    "email": kullanici.email,
                    "sinif_seviyesi": ogrenci_profili.sinif_seviyesi,
                    "okul_adi": ogrenci_profili.okul_adi,
                    "hedef_sinav": ogrenci_profili.hedef_sinav.value
                    if ogrenci_profili.hedef_sinav
                    else None,
                    "son_giris": kullanici.son_giris,
                    "performans": son_performans,
                    "aktif": kullanici.aktif,
                }

                ogrenci_listesi.append(ogrenci_verisi)

            # Performansa göre sırala (en yüksek net önce)
            ogrenci_listesi.sort(
                key=lambda x: x["performans"]["ortalama_net"], reverse=True
            )

            return ogrenci_listesi

        except Exception as e:
            raise ValueError(f"Öğrenci listesi alınamadı: {str(e)}")

    async def ogrenci_detay_performans(
        self, ogretmen_id: str, ogrenci_id: str
    ) -> Dict[str, Any]:
        """Belirli bir öğrencinin detaylı performans analizi"""
        try:
            # Yetki kontrolü
            if not await self._ogretmen_ogrenci_yetkisi_kontrol(
                ogretmen_id, ogrenci_id
            ):
                raise ValueError("Bu öğrenciye erişim yetkiniz yok")

            # Öğrenci bilgilerini getir
            ogrenci_profili = await kullanici_servisi.ogrenci_profili_getir(ogrenci_id)
            kullanici = await kullanici_servisi.kullanici_getir(
                ogrenci_profili.kullanici_id
            )

            # Tüm sınavları getir
            tum_sinavlar = await sinav_motoru_servisi.ogrenci_sinavlari(ogrenci_id)

            # Sınav sonuçlarını analiz et
            sinav_sonuclari = []
            konu_performanslari = {}
            net_trendi = []

            for sinav in tum_sinavlar:
                sonuc = await sinav_motoru_servisi.sonuc_getir(sinav.sinav_id)
                if sonuc:
                    sinav_sonuclari.append(
                        {
                            "sinav_id": sinav.sinav_id,
                            "sinav_tipi": sinav.sinav_tipi.value,
                            "tarih": sinav.olusturma_tarihi,
                            "net_sayisi": sonuc.net_sayisi,
                            "ham_puan": sonuc.ham_puan,
                            "dogru": sonuc.dogru_sayisi,
                            "yanlis": sonuc.yanlis_sayisi,
                            "bos": sonuc.bos_sayisi,
                        }
                    )

                    # Net trendi için
                    net_trendi.append(
                        {
                            "tarih": sinav.olusturma_tarihi.strftime("%Y-%m-%d"),
                            "net": sonuc.net_sayisi,
                        }
                    )

                    # Konu performansları
                    for konu_perf in sonuc.konu_performanslari:
                        if konu_perf.konu not in konu_performanslari:
                            konu_performanslari[konu_perf.konu] = {
                                "toplam_soru": 0,
                                "toplam_dogru": 0,
                                "sinav_sayisi": 0,
                            }

                        konu_performanslari[konu_perf.konu][
                            "toplam_soru"
                        ] += konu_perf.toplam_soru
                        konu_performanslari[konu_perf.konu][
                            "toplam_dogru"
                        ] += konu_perf.dogru_sayisi
                        konu_performanslari[konu_perf.konu]["sinav_sayisi"] += 1

            # Konu başarı yüzdelerini hesapla
            konu_basari_yuzdesi = {}
            for konu, stats in konu_performanslari.items():
                if stats["toplam_soru"] > 0:
                    konu_basari_yuzdesi[konu] = (
                        stats["toplam_dogru"] / stats["toplam_soru"]
                    ) * 100

            # Zayıf ve güçlü konuları belirle
            zayif_konular = [
                konu for konu, yuzde in konu_basari_yuzdesi.items() if yuzde < 50
            ]
            guclu_konular = [
                konu for konu, yuzde in konu_basari_yuzdesi.items() if yuzde > 80
            ]

            # Gelişim trendi analizi
            gelisim_trendi = "sabit"
            if len(net_trendi) >= 3:
                son_uc = [x["net"] for x in net_trendi[-3:]]
                if son_uc[-1] > son_uc[0]:
                    gelisim_trendi = "artan"
                elif son_uc[-1] < son_uc[0]:
                    gelisim_trendi = "azalan"

            return {
                "ogrenci_bilgileri": {
                    "ad_soyad": kullanici.ad_soyad,
                    "email": kullanici.email,
                    "sinif_seviyesi": ogrenci_profili.sinif_seviyesi,
                    "hedef_sinav": ogrenci_profili.hedef_sinav.value
                    if ogrenci_profili.hedef_sinav
                    else None,
                    "hedef_universiteler": ogrenci_profili.hedef_universiteler,
                },
                "genel_istatistikler": {
                    "toplam_sinav": len(sinav_sonuclari),
                    "ortalama_net": sum([s["net_sayisi"] for s in sinav_sonuclari])
                    / len(sinav_sonuclari)
                    if sinav_sonuclari
                    else 0,
                    "en_yuksek_net": max([s["net_sayisi"] for s in sinav_sonuclari])
                    if sinav_sonuclari
                    else 0,
                    "gelisim_trendi": gelisim_trendi,
                },
                "sinav_gecmisi": sinav_sonuclari,
                "net_trendi": net_trendi,
                "konu_performanslari": konu_basari_yuzdesi,
                "zayif_konular": zayif_konular,
                "guclu_konular": guclu_konular,
                "oneriler": await self._ogrenci_onerileri_olustur(
                    ogrenci_id, zayif_konular, guclu_konular
                ),
            }

        except Exception as e:
            raise ValueError(f"Öğrenci performans verisi alınamadı: {str(e)}")

    async def sinif_raporu_olustur(
        self, ogretmen_id: str, rapor_parametreleri: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sınıf geneli için rapor oluştur"""
        try:
            # Öğrenci listesini getir
            ogrenci_listesi = await self.ogrenci_listesi_getir(ogretmen_id)

            if not ogrenci_listesi:
                raise ValueError("Rapor oluşturmak için öğrenci bulunamadı")

            # Rapor parametrelerini al
            baslangic_tarihi = rapor_parametreleri.get("baslangic_tarihi")
            bitis_tarihi = rapor_parametreleri.get("bitis_tarihi")
            sinav_tipi = rapor_parametreleri.get("sinav_tipi")

            # Tarih aralığını ayarla
            if not baslangic_tarihi:
                baslangic_tarihi = datetime.now() - timedelta(days=30)
            if not bitis_tarihi:
                bitis_tarihi = datetime.now()

            # Sınıf istatistikleri
            sinif_istatistikleri = {
                "toplam_ogrenci": len(ogrenci_listesi),
                "aktif_ogrenci": len([o for o in ogrenci_listesi if o["aktif"]]),
                "ortalama_net": 0,
                "en_yuksek_net": 0,
                "en_dusuk_net": 0,
                "standart_sapma": 0,
            }

            # Konu bazlı sınıf performansı
            konu_performanslari = {}
            tum_netler = []

            for ogrenci in ogrenci_listesi:
                ogrenci_id = ogrenci["ogrenci_id"]

                # Öğrencinin sınavlarını getir
                ogrenci_sinavlari = await sinav_motoru_servisi.ogrenci_sinavlari(
                    ogrenci_id
                )

                for sinav in ogrenci_sinavlari:
                    # Tarih ve tür filtresi
                    if baslangic_tarihi <= sinav.olusturma_tarihi <= bitis_tarihi:
                        if not sinav_tipi or sinav.sinav_tipi.value == sinav_tipi:
                            sonuc = await sinav_motoru_servisi.sonuc_getir(
                                sinav.sinav_id
                            )
                            if sonuc:
                                tum_netler.append(sonuc.net_sayisi)

                                # Konu performansları
                                for konu_perf in sonuc.konu_performanslari:
                                    if konu_perf.konu not in konu_performanslari:
                                        konu_performanslari[konu_perf.konu] = {
                                            "toplam_soru": 0,
                                            "toplam_dogru": 0,
                                            "ogrenci_sayisi": 0,
                                        }

                                    konu_performanslari[konu_perf.konu][
                                        "toplam_soru"
                                    ] += konu_perf.toplam_soru
                                    konu_performanslari[konu_perf.konu][
                                        "toplam_dogru"
                                    ] += konu_perf.dogru_sayisi
                                    konu_performanslari[konu_perf.konu][
                                        "ogrenci_sayisi"
                                    ] += 1

            # İstatistikleri hesapla
            if tum_netler:
                sinif_istatistikleri["ortalama_net"] = sum(tum_netler) / len(tum_netler)
                sinif_istatistikleri["en_yuksek_net"] = max(tum_netler)
                sinif_istatistikleri["en_dusuk_net"] = min(tum_netler)

                # Standart sapma hesapla
                ortalama = sinif_istatistikleri["ortalama_net"]
                varyans = sum([(x - ortalama) ** 2 for x in tum_netler]) / len(
                    tum_netler
                )
                sinif_istatistikleri["standart_sapma"] = varyans**0.5

            # Konu başarı yüzdelerini hesapla
            konu_basari_yuzdesi = {}
            for konu, stats in konu_performanslari.items():
                if stats["toplam_soru"] > 0:
                    konu_basari_yuzdesi[konu] = (
                        stats["toplam_dogru"] / stats["toplam_soru"]
                    ) * 100

            # En zayıf ve en güçlü konuları belirle
            if konu_basari_yuzdesi:
                en_zayif_konu = min(konu_basari_yuzdesi.items(), key=lambda x: x[1])
                en_guclu_konu = max(konu_basari_yuzdesi.items(), key=lambda x: x[1])
            else:
                en_zayif_konu = ("Veri yok", 0)
                en_guclu_konu = ("Veri yok", 0)

            # Rapor ID oluştur ve kaydet
            rapor_id = str(uuid.uuid4())
            rapor_verisi = {
                "rapor_id": rapor_id,
                "ogretmen_id": ogretmen_id,
                "olusturma_tarihi": datetime.now(),
                "rapor_donemi": {"baslangic": baslangic_tarihi, "bitis": bitis_tarihi},
                "sinif_istatistikleri": sinif_istatistikleri,
                "konu_performanslari": konu_basari_yuzdesi,
                "en_zayif_konu": en_zayif_konu,
                "en_guclu_konu": en_guclu_konu,
                "ogrenci_sayisi": len(ogrenci_listesi),
                "sinav_sayisi": len(tum_netler),
                "oneriler": await self._sinif_onerileri_olustur(
                    konu_basari_yuzdesi, sinif_istatistikleri
                ),
            }

            self.sinif_raporlari[rapor_id] = rapor_verisi

            return rapor_verisi

        except Exception as e:
            raise ValueError(f"Sınıf raporu oluşturulamadı: {str(e)}")

    async def bildirim_gonder(
        self, ogretmen_id: str, bildirim_verisi: Dict[str, Any]
    ) -> bool:
        """Öğretmen bildirimi gönder"""
        try:
            bildirim = {
                "bildirim_id": str(uuid.uuid4()),
                "baslik": bildirim_verisi.get("baslik", ""),
                "mesaj": bildirim_verisi.get("mesaj", ""),
                "tip": bildirim_verisi.get(
                    "tip", "bilgi"
                ),  # bilgi, uyari, basari, hata
                "olusturma_tarihi": datetime.now(),
                "okundu": False,
            }

            if ogretmen_id not in self.ogretmen_bildirimleri:
                self.ogretmen_bildirimleri[ogretmen_id] = []

            self.ogretmen_bildirimleri[ogretmen_id].append(bildirim)

            # En fazla 50 bildirim tut
            if len(self.ogretmen_bildirimleri[ogretmen_id]) > 50:
                self.ogretmen_bildirimleri[ogretmen_id] = self.ogretmen_bildirimleri[
                    ogretmen_id
                ][-50:]

            return True

        except Exception as e:
            print(f"Bildirim gönderme hatası: {e}")
            return False

    async def bildirimler_getir(
        self, ogretmen_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Öğretmen bildirimlerini getir"""
        bildirimler = self.ogretmen_bildirimleri.get(ogretmen_id, [])

        # En yeni bildirimler önce
        bildirimler.sort(key=lambda x: x["olusturma_tarihi"], reverse=True)

        return bildirimler[:limit]

    async def bildirim_okundu_isaretle(
        self, ogretmen_id: str, bildirim_id: str
    ) -> bool:
        """Bildirimi okundu olarak işaretle"""
        bildirimler = self.ogretmen_bildirimleri.get(ogretmen_id, [])

        for bildirim in bildirimler:
            if bildirim["bildirim_id"] == bildirim_id:
                bildirim["okundu"] = True
                return True

        return False

    async def _demo_ogrenci_iliskileri_olustur(self, ogretmen_id: str):
        """Demo öğrenci-öğretmen ilişkileri oluştur"""
        # Mevcut öğrencileri getir
        tum_kullanicilar = await kullanici_servisi.kullanici_listesi(
            rol=KullaniciRolu.OGRENCI
        )

        # İlk 5 öğrenciyi bu öğretmene ata
        ogrenci_ids = []
        for kullanici in tum_kullanicilar[:5]:
            # Öğrenci profilini kontrol et
            for ogrenci_id, profil in kullanici_servisi.ogrenci_profilleri.items():
                if profil.kullanici_id == kullanici.kullanici_id:
                    ogrenci_ids.append(ogrenci_id)
                    break

        self.sinif_ogrenci_iliskileri[ogretmen_id] = ogrenci_ids

    async def _ogrenci_son_performans(self, ogrenci_id: str) -> Dict[str, Any]:
        """Öğrencinin son performans verilerini getir"""
        try:
            sinavlar = await sinav_motoru_servisi.ogrenci_sinavlari(ogrenci_id)

            if not sinavlar:
                return {
                    "ortalama_net": 0,
                    "son_sinav_tarihi": None,
                    "toplam_sinav": 0,
                    "gelisim_trendi": "veri_yok",
                }

            # Son 5 sınavın sonuçlarını al
            son_sinavlar = sorted(
                sinavlar, key=lambda x: x.olusturma_tarihi, reverse=True
            )[:5]

            toplam_net = 0
            sinav_sayisi = 0

            for sinav in son_sinavlar:
                sonuc = await sinav_motoru_servisi.sonuc_getir(sinav.sinav_id)
                if sonuc:
                    toplam_net += sonuc.net_sayisi
                    sinav_sayisi += 1

            ortalama_net = toplam_net / sinav_sayisi if sinav_sayisi > 0 else 0

            return {
                "ortalama_net": round(ortalama_net, 2),
                "son_sinav_tarihi": son_sinavlar[0].olusturma_tarihi
                if son_sinavlar
                else None,
                "toplam_sinav": len(sinavlar),
                "gelisim_trendi": "sabit",  # Basit implementasyon
            }

        except Exception:
            return {
                "ortalama_net": 0,
                "son_sinav_tarihi": None,
                "toplam_sinav": 0,
                "gelisim_trendi": "veri_yok",
            }

    async def _ogretmen_ogrenci_yetkisi_kontrol(
        self, ogretmen_id: str, ogrenci_id: str
    ) -> bool:
        """Öğretmenin öğrenciye erişim yetkisi var mı kontrol et"""
        ogrenci_ids = self.sinif_ogrenci_iliskileri.get(ogretmen_id, [])
        return ogrenci_id in ogrenci_ids

    async def _ogrenci_onerileri_olustur(
        self, ogrenci_id: str, zayif_konular: List[str], guclu_konular: List[str]
    ) -> List[str]:
        """Öğrenci için öneriler oluştur"""
        oneriler = []

        if zayif_konular:
            oneriler.append(
                f"Bu konularda daha fazla çalışma yapılması önerilir: {', '.join(zayif_konular[:3])}"
            )
            oneriler.append(
                "Zayıf konular için ek kaynak ve video içerikleri incelenebilir"
            )

        if guclu_konular:
            oneriler.append(f"Bu konularda başarılı: {', '.join(guclu_konular[:3])}")
            oneriler.append("Güçlü konularda pekiştirme soruları çözülebilir")

        if not zayif_konular and not guclu_konular:
            oneriler.append("Daha fazla sınav çözerek performans analizi yapılabilir")

        return oneriler

    async def _sinif_onerileri_olustur(
        self,
        konu_performanslari: Dict[str, float],
        sinif_istatistikleri: Dict[str, Any],
    ) -> List[str]:
        """Sınıf için öneriler oluştur"""
        oneriler = []

        if konu_performanslari:
            # En zayıf konuları bul
            zayif_konular = [
                konu for konu, yuzde in konu_performanslari.items() if yuzde < 50
            ]

            if zayif_konular:
                oneriler.append(
                    f"Sınıf genelinde bu konulara odaklanılması önerilir: {', '.join(zayif_konular[:3])}"
                )

            # Ortalama kontrolü
            ortalama_net = sinif_istatistikleri.get("ortalama_net", 0)
            if ortalama_net < 30:
                oneriler.append(
                    "Sınıf ortalaması düşük, temel konulara daha fazla zaman ayrılmalı"
                )
            elif ortalama_net > 60:
                oneriler.append(
                    "Sınıf başarılı, ileri seviye sorularla pekiştirme yapılabilir"
                )

        if not oneriler:
            oneriler.append("Düzenli sınav takibi ile performans artırılabilir")

        return oneriler


# Global servis instance
ogretmen_servisi = OgretmenServisi()
