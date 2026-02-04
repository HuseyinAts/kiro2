"""
Hibrit Öğrenme Stili Servisi
VARK + Felder-Silverman hibrit öğrenme stili tespiti
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LearningStyleService:
    """
    Hibrit öğrenme stili servisi
    VARK + Felder-Silverman = 64 farklı öğrenme profili
    """
    
    def __init__(self):
        """Servisi başlat"""
        self.student_profiles = {}
        
        # VARK boyutları
        self.vark_dimensions = ["visual", "auditory", "reading", "kinesthetic"]
        
        # Felder-Silverman boyutları
        self.felder_dimensions = [
            "active_reflective",
            "sensing_intuitive", 
            "visual_verbal",
            "sequential_global"
        ]
    
    async def detect_learning_style(
        self,
        student_id: str,
        behavioral_data: Dict[str, Any],
        questionnaire_responses: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Hibrit öğrenme stilini tespit et
        """
        try:
            # Mock VARK profili
            vark_profile = {
                "visual": 0.7,
                "auditory": 0.5,
                "reading": 0.8,
                "kinesthetic": 0.4
            }
            
            # Mock Felder-Silverman profili
            felder_profile = {
                "active_reflective": 0.3,
                "sensing_intuitive": -0.2,
                "visual_verbal": 0.6,
                "sequential_global": -0.4
            }
            
            # Hibrit kod oluştur
            hibrit_kod = self._generate_hibrit_code(vark_profile, felder_profile)
            
            # Profil özeti
            hibrit_profil = {
                "student_id": student_id,
                "vark_profili": vark_profile,
                "felder_silverman_profili": felder_profile,
                "hibrit_kod": hibrit_kod,
                "dominant_vark_stili": max(vark_profile, key=vark_profile.get),
                "dominant_felder_boyutu": max(felder_profile, key=lambda k: abs(felder_profile[k])),
                "guven_seviyesi": 0.82,
                "tespit_tarihi": datetime.now().isoformat(),
                "profil_aciklamasi": self._get_profile_description(hibrit_kod)
            }
            
            # Cache'e kaydet
            self.student_profiles[student_id] = hibrit_profil
            
            logger.info(f"Hibrit öğrenme stili tespit edildi - Öğrenci: {student_id}, Kod: {hibrit_kod}")
            
            return hibrit_profil
            
        except Exception as e:
            logger.error(f"Öğrenme stili tespit hatası - Öğrenci: {student_id}, Hata: {str(e)}")
            raise
    
    async def get_learning_recommendations(
        self,
        student_id: str,
        subject: str = "genel"
    ) -> List[Dict[str, Any]]:
        """
        Öğrenme stiline göre öneriler oluştur
        """
        try:
            profile = self.student_profiles.get(student_id)
            if not profile:
                # Profil yoksa tespit et
                profile = await self.detect_learning_style(student_id, {})
            
            recommendations = []
            
            # VARK tabanlı öneriler
            vark_profile = profile["vark_profili"]
            dominant_vark = max(vark_profile, key=vark_profile.get)
            
            if dominant_vark == "visual":
                recommendations.append({
                    "tip": "görsel_materyaller",
                    "açıklama": "Diyagramlar, grafikler ve görsel materyaller kullanın",
                    "öncelik": "yüksek"
                })
            elif dominant_vark == "auditory":
                recommendations.append({
                    "tip": "sesli_çalışma",
                    "açıklama": "Sesli okuma, müzik eşliğinde çalışma ve tartışma grupları",
                    "öncelik": "yüksek"
                })
            elif dominant_vark == "reading":
                recommendations.append({
                    "tip": "metin_tabanlı",
                    "açıklama": "Kitap okuma, not alma ve yazılı özetler",
                    "öncelik": "yüksek"
                })
            elif dominant_vark == "kinesthetic":
                recommendations.append({
                    "tip": "uygulamalı_öğrenme",
                    "açıklama": "Deneyler, uygulamalı çalışmalar ve hareket içeren aktiviteler",
                    "öncelik": "yüksek"
                })
            
            # Felder-Silverman tabanlı öneriler
            felder_profile = profile["felder_silverman_profili"]
            
            if felder_profile["active_reflective"] > 0:
                recommendations.append({
                    "tip": "aktif_öğrenme",
                    "açıklama": "Grup çalışması ve tartışma odaklı öğrenme",
                    "öncelik": "orta"
                })
            else:
                recommendations.append({
                    "tip": "yansıtıcı_öğrenme",
                    "açıklama": "Bireysel düşünme ve analiz zamanı ayırın",
                    "öncelik": "orta"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Öğrenme önerileri hatası - Öğrenci: {student_id}, Hata: {str(e)}")
            raise
    
    def _generate_hibrit_code(
        self,
        vark_profile: Dict[str, float],
        felder_profile: Dict[str, float]
    ) -> str:
        """
        Hibrit kod oluştur (64 kombinasyondan biri)
        """
        # VARK kodu
        vark_code = ""
        for dimension, score in vark_profile.items():
            if score > 0.6:
                vark_code += dimension[0].upper()
        
        if not vark_code:
            vark_code = "M"  # Mixed
        
        # Felder-Silverman kodu
        felder_code = ""
        
        # Active/Reflective
        if felder_profile["active_reflective"] > 0.3:
            felder_code += "A"
        elif felder_profile["active_reflective"] < -0.3:
            felder_code += "R"
        else:
            felder_code += "M"
        
        # Sensing/Intuitive
        if felder_profile["sensing_intuitive"] > 0.3:
            felder_code += "S"
        elif felder_profile["sensing_intuitive"] < -0.3:
            felder_code += "I"
        else:
            felder_code += "M"
        
        # Visual/Verbal
        if felder_profile["visual_verbal"] > 0.3:
            felder_code += "V"
        elif felder_profile["visual_verbal"] < -0.3:
            felder_code += "B"
        else:
            felder_code += "M"
        
        # Sequential/Global
        if felder_profile["sequential_global"] > 0.3:
            felder_code += "S"
        elif felder_profile["sequential_global"] < -0.3:
            felder_code += "G"
        else:
            felder_code += "M"
        
        return f"{vark_code}-{felder_code}"
    
    def _get_profile_description(self, hibrit_kod: str) -> str:
        """
        Hibrit kod açıklaması
        """
        return f"Hibrit öğrenme profili {hibrit_kod}: Bu profil, VARK ve Felder-Silverman modellerinin birleşiminden oluşur."
    
    async def get_student_profile(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Öğrenci profilini getir
        """
        return self.student_profiles.get(student_id)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        Servis istatistikleri
        """
        return {
            "toplam_profil_sayisi": len(self.student_profiles),
            "vark_boyutlari": self.vark_dimensions,
            "felder_boyutlari": self.felder_dimensions,
            "toplam_kombinasyon": 64
        }