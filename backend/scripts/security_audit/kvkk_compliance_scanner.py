#!/usr/bin/env python3
"""
KVKK (Kisisel Verilerin Korunmasi Kanunu) Compliance Scanner
KIRO2 Platform - Task 144

Bu script KVKK uyumluluk kontrollerini gerceklestirir:
- 144.1 KVKK compliance checklist
- 144.2 Privacy policy ve terms of service
- 144.3 Audit logging validation
- 144.4 PII data handling audit
"""

import asyncio
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class ComplianceStatus(Enum):
    COMPLIANT = "UYUMLU"
    NON_COMPLIANT = "UYUMSUZ"
    PARTIAL = "KISMI"
    NEEDS_REVIEW = "INCELEME_GEREKLI"
    NOT_APPLICABLE = "UYGULANAMAZ"


class Severity(Enum):
    CRITICAL = "KRITIK"
    HIGH = "YUKSEK"
    MEDIUM = "ORTA"
    LOW = "DUSUK"
    INFO = "BILGI"


@dataclass
class KVKKFinding:
    """KVKK compliance finding"""
    article: str
    requirement: str
    status: ComplianceStatus
    severity: Severity
    description: str
    file_path: str | None = None
    evidence: str = ""
    recommendation: str = ""


@dataclass
class KVKKReport:
    """KVKK compliance report"""
    scan_date: str = field(default_factory=lambda: datetime.now().isoformat())
    platform: str = "KIRO2 - YKS AI Egitim Platformu"
    findings: list[KVKKFinding] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def add_finding(self, finding: KVKKFinding) -> None:
        self.findings.append(finding)

    def generate_summary(self) -> dict:
        self.summary = {
            "total_checks": len(self.findings),
            "compliant": len([f for f in self.findings if f.status == ComplianceStatus.COMPLIANT]),
            "non_compliant": len([f for f in self.findings if f.status == ComplianceStatus.NON_COMPLIANT]),
            "partial": len([f for f in self.findings if f.status == ComplianceStatus.PARTIAL]),
            "needs_review": len([f for f in self.findings if f.status == ComplianceStatus.NEEDS_REVIEW]),
            "critical": len([f for f in self.findings if f.severity == Severity.CRITICAL]),
            "high": len([f for f in self.findings if f.severity == Severity.HIGH]),
            "compliance_score": 0,
        }
        total = len(self.findings)
        if total > 0:
            compliant = self.summary["compliant"]
            partial = self.summary["partial"] * 0.5
            self.summary["compliance_score"] = int((compliant + partial) / total * 100)
        return self.summary


class KVKKComplianceScanner:
    """KVKK 6698 Sayili Kanun Uyumluluk Tarayicisi"""

    def __init__(self, backend_path: str, frontend_path: str = None):
        self.backend_path = Path(backend_path)
        self.frontend_path = Path(frontend_path) if frontend_path else self.backend_path.parent / "frontend"
        self.report = KVKKReport()

    async def run_full_scan(self) -> KVKKReport:
        """Tam KVKK uyumluluk taramasi"""
        print("[KVKK] KIRO2 KVKK Uyumluluk Denetimi Baslatildi")
        print("=" * 60)

        # Madde 5: Kisisel Verilerin Islenmesi
        await self.check_article_5_data_processing()

        # Madde 6: Ozel Nitelikli Kisisel Veriler
        await self.check_article_6_special_categories()

        # Madde 7: Kisisel Verilerin Silinmesi
        await self.check_article_7_data_deletion()

        # Madde 10: Aydinlatma Yukumlulugu
        await self.check_article_10_transparency()

        # Madde 11: Ilgili Kisinin Haklari
        await self.check_article_11_data_subject_rights()

        # Madde 12: Veri Guvenligi
        await self.check_article_12_data_security()

        # Egitim Spesifik Kontroller
        await self.check_student_data_protection()

        # Audit Logging
        await self.check_audit_logging()

        # PII Data Handling
        await self.check_pii_handling()

        self.report.generate_summary()
        return self.report

    async def check_article_5_data_processing(self) -> None:
        """Madde 5: Kisisel Verilerin Islenmesi Sartlari"""
        print("\n[MADDE 5] Kisisel Verilerin Islenmesi Kontrolu...")

        # Riza (Consent) mekanizmasi kontrolu
        consent_patterns = [
            r"consent",
            r"riza",
            r"onay",
            r"izin",
            r"kabul",
        ]

        consent_found = False
        consent_files = []

        for py_file in self.backend_path.rglob("*.py"):
            if "venv" in str(py_file) or "test" in str(py_file).lower():
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                if any(re.search(p, content) for p in consent_patterns):
                    consent_found = True
                    consent_files.append(str(py_file.name))
            except Exception:
                pass

        if consent_found:
            self.report.add_finding(KVKKFinding(
                article="Madde 5.1",
                requirement="Acik riza mekanizmasi",
                status=ComplianceStatus.COMPLIANT,
                severity=Severity.INFO,
                description="Riza/consent mekanizmasi kodda tespit edildi",
                evidence=f"Bulunan dosyalar: {', '.join(consent_files[:5])}",
            ))
        else:
            self.report.add_finding(KVKKFinding(
                article="Madde 5.1",
                requirement="Acik riza mekanizmasi",
                status=ComplianceStatus.NON_COMPLIANT,
                severity=Severity.CRITICAL,
                description="Acik riza mekanizmasi bulunamadi",
                recommendation="Kullanici riza yonetim sistemi implement edilmeli",
            ))

        # KVKK modulu kontrolu
        kvkk_files = list(self.backend_path.glob("**/kvkk*.py"))
        if kvkk_files:
            self.report.add_finding(KVKKFinding(
                article="Madde 5",
                requirement="KVKK modulu",
                status=ComplianceStatus.COMPLIANT,
                severity=Severity.INFO,
                description=f"KVKK modulu mevcut: {len(kvkk_files)} dosya",
                file_path=str(kvkk_files[0]),
            ))
        else:
            self.report.add_finding(KVKKFinding(
                article="Madde 5",
                requirement="KVKK modulu",
                status=ComplianceStatus.NON_COMPLIANT,
                severity=Severity.HIGH,
                description="Ayri KVKK modulu bulunamadi",
                recommendation="backend/core/kvkk_compliance.py olusturulmali",
            ))

        print("  [OK] Madde 5 kontrolu tamamlandi")

    async def check_article_6_special_categories(self) -> None:
        """Madde 6: Ozel Nitelikli Kisisel Veriler"""
        print("\n[MADDE 6] Ozel Nitelikli Veriler Kontrolu...")

        # Ogrenci egitim verileri ozel kategori
        special_data_patterns = [
            (r"tc_kimlik|tcno|tckn", "TC Kimlik No"),
            (r"saglik|health|disability|engel", "Saglik Verisi"),
            (r"biometric|biyometrik|parmak_izi|yuz_tanima", "Biyometrik Veri"),
            (r"din|religion|ethnic|etnik", "Din/Etnik Veri"),
        ]

        for pattern, data_type in special_data_patterns:
            found_files = []
            for py_file in self.backend_path.rglob("*.py"):
                if "venv" in str(py_file) or "test" in str(py_file).lower():
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                    if re.search(pattern, content):
                        found_files.append(py_file.name)
                except Exception:
                    pass

            if found_files:
                self.report.add_finding(KVKKFinding(
                    article="Madde 6",
                    requirement=f"Ozel kategori veri: {data_type}",
                    status=ComplianceStatus.NEEDS_REVIEW,
                    severity=Severity.HIGH,
                    description=f"{data_type} verisi isleniyor olabilir",
                    evidence=f"Dosyalar: {', '.join(found_files[:3])}",
                    recommendation="Acik riza alindigindan emin olunmali",
                ))

        print("  [OK] Madde 6 kontrolu tamamlandi")

    async def check_article_7_data_deletion(self) -> None:
        """Madde 7: Kisisel Verilerin Silinmesi, Yok Edilmesi, Anonim Hale Getirilmesi"""
        print("\n[MADDE 7] Veri Silme/Anonimizasyon Kontrolu...")

        # Silme mekanizmasi
        delete_patterns = [
            r"delete.*user|user.*delete",
            r"anonymize|anonimize|anonim",
            r"soft_delete|softdelete",
            r"hard_delete|harddelete",
            r"data_retention|veri_saklama",
        ]

        deletion_features = []
        for py_file in self.backend_path.rglob("*.py"):
            if "venv" in str(py_file) or "test" in str(py_file).lower():
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                for pattern in delete_patterns:
                    if re.search(pattern, content):
                        deletion_features.append(f"{py_file.name}:{pattern}")
                        break
            except Exception:
                pass

        if len(deletion_features) >= 2:
            self.report.add_finding(KVKKFinding(
                article="Madde 7",
                requirement="Veri silme mekanizmasi",
                status=ComplianceStatus.COMPLIANT,
                severity=Severity.INFO,
                description="Veri silme mekanizmasi mevcut",
                evidence=f"Bulunan: {', '.join(deletion_features[:5])}",
            ))
        else:
            self.report.add_finding(KVKKFinding(
                article="Madde 7",
                requirement="Veri silme mekanizmasi",
                status=ComplianceStatus.NON_COMPLIANT,
                severity=Severity.CRITICAL,
                description="Tam kapsamli veri silme mekanizmasi eksik",
                recommendation="Right to be forgotten (unutulma hakki) implement edilmeli",
            ))

        # Anonimizasyon kontrolu
        anon_patterns = [r"anonymize", r"mask", r"pseudonymize", r"hash.*pii"]
        anon_found = False

        for py_file in self.backend_path.rglob("*.py"):
            if "venv" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                if any(re.search(p, content) for p in anon_patterns):
                    anon_found = True
                    break
            except Exception:
                pass

        if anon_found:
            self.report.add_finding(KVKKFinding(
                article="Madde 7",
                requirement="Anonimizasyon/Maskeleme",
                status=ComplianceStatus.COMPLIANT,
                severity=Severity.INFO,
                description="Anonimizasyon mekanizmasi tespit edildi",
            ))
        else:
            self.report.add_finding(KVKKFinding(
                article="Madde 7",
                requirement="Anonimizasyon/Maskeleme",
                status=ComplianceStatus.PARTIAL,
                severity=Severity.MEDIUM,
                description="Anonimizasyon mekanizmasi acikca tanimlanmamis",
                recommendation="PII maskeleme ve anonimizasyon fonksiyonlari eklenmeli",
            ))

        print("  [OK] Madde 7 kontrolu tamamlandi")

    async def check_article_10_transparency(self) -> None:
        """Madde 10: Aydinlatma Yukumlulugu"""
        print("\n[MADDE 10] Aydinlatma Yukumlulugu Kontrolu...")

        # Privacy policy / Gizlilik politikasi kontrolu
        privacy_keywords = [
            "privacy_policy",
            "gizlilik_politikasi",
            "aydinlatma_metni",
            "kvkk_aydinlatma",
            "disclosure",
        ]

        privacy_found = False
        for py_file in self.backend_path.rglob("*.py"):
            if "venv" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                if any(kw in content for kw in privacy_keywords):
                    privacy_found = True
                    break
            except Exception:
                pass

        # Frontend kontrolu
        if self.frontend_path.exists():
            for file in self.frontend_path.rglob("*.tsx"):
                try:
                    content = file.read_text(encoding="utf-8", errors="ignore").lower()
                    if any(kw in content for kw in ["privacy", "gizlilik", "kvkk"]):
                        privacy_found = True
                        break
                except Exception:
                    pass

        if privacy_found:
            self.report.add_finding(KVKKFinding(
                article="Madde 10",
                requirement="Aydinlatma metni",
                status=ComplianceStatus.COMPLIANT,
                severity=Severity.INFO,
                description="Gizlilik politikasi/aydinlatma metni referansi bulundu",
            ))
        else:
            self.report.add_finding(KVKKFinding(
                article="Madde 10",
                requirement="Aydinlatma metni",
                status=ComplianceStatus.NON_COMPLIANT,
                severity=Severity.CRITICAL,
                description="Aydinlatma metni bulunamadi",
                recommendation="KVKK aydinlatma metni olusturulmali ve kullanicilara sunulmali",
            ))

        print("  [OK] Madde 10 kontrolu tamamlandi")

    async def check_article_11_data_subject_rights(self) -> None:
        """Madde 11: Ilgili Kisinin Haklari"""
        print("\n[MADDE 11] Veri Sahibi Haklari Kontrolu...")

        # Haklar listesi
        rights = [
            ("data_export|export.*user|download.*data|veri_tasima", "Veri Tasinabilirligi"),
            ("access.*request|get.*my.*data|verilerime_eris", "Veri Erisim Hakki"),
            ("rectification|correct.*data|duzeltme", "Duzeltme Hakki"),
            ("restriction|processing.*limit|isleme.*sinirla", "Islemeyi Sinirlandirma"),
            ("object.*processing|itiraz", "Itiraz Hakki"),
        ]

        rights_implemented = 0
        for pattern, right_name in rights:
            found = False
            for py_file in self.backend_path.rglob("*.py"):
                if "venv" in str(py_file):
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                    if re.search(pattern, content):
                        found = True
                        break
                except Exception:
                    pass

            status = ComplianceStatus.COMPLIANT if found else ComplianceStatus.NON_COMPLIANT
            severity = Severity.INFO if found else Severity.HIGH

            self.report.add_finding(KVKKFinding(
                article="Madde 11",
                requirement=right_name,
                status=status,
                severity=severity,
                description=f"{right_name} {'implement edilmis' if found else 'eksik'}",
                recommendation="" if found else f"{right_name} icin API endpoint eklenmeli",
            ))

            if found:
                rights_implemented += 1

        print(f"  [OK] Madde 11 kontrolu tamamlandi ({rights_implemented}/5 hak)")

    async def check_article_12_data_security(self) -> None:
        """Madde 12: Veri Guvenligi"""
        print("\n[MADDE 12] Veri Guvenligi Kontrolu...")

        # Sifreleme kontrolu
        encryption_patterns = [
            r"encrypt|crypt|aes|rsa|fernet",
            r"bcrypt|argon2|pbkdf2",
            r"ssl|tls|https",
        ]

        encryption_found = 0
        for pattern in encryption_patterns:
            for py_file in self.backend_path.rglob("*.py"):
                if "venv" in str(py_file):
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                    if re.search(pattern, content):
                        encryption_found += 1
                        break
                except Exception:
                    pass

        if encryption_found >= 2:
            self.report.add_finding(KVKKFinding(
                article="Madde 12",
                requirement="Veri sifreleme",
                status=ComplianceStatus.COMPLIANT,
                severity=Severity.INFO,
                description="Sifreleme mekanizmalari tespit edildi",
            ))
        else:
            self.report.add_finding(KVKKFinding(
                article="Madde 12",
                requirement="Veri sifreleme",
                status=ComplianceStatus.PARTIAL,
                severity=Severity.HIGH,
                description="Sifreleme mekanizmasi eksik veya yetersiz",
                recommendation="At-rest ve in-transit sifreleme saglanmali",
            ))

        # Access control
        access_patterns = [
            r"rbac|role.*based",
            r"permission|yetki",
            r"authorization|yetkilendirme",
        ]

        access_control_found = False
        for pattern in access_patterns:
            for py_file in self.backend_path.rglob("*.py"):
                if "venv" in str(py_file):
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                    if re.search(pattern, content):
                        access_control_found = True
                        break
                except Exception:
                    pass
            if access_control_found:
                break

        if access_control_found:
            self.report.add_finding(KVKKFinding(
                article="Madde 12",
                requirement="Erisim kontrolu",
                status=ComplianceStatus.COMPLIANT,
                severity=Severity.INFO,
                description="Erisim kontrol mekanizmasi mevcut",
            ))
        else:
            self.report.add_finding(KVKKFinding(
                article="Madde 12",
                requirement="Erisim kontrolu",
                status=ComplianceStatus.NON_COMPLIANT,
                severity=Severity.CRITICAL,
                description="Erisim kontrol mekanizmasi bulunamadi",
                recommendation="RBAC sistemi implement edilmeli",
            ))

        print("  [OK] Madde 12 kontrolu tamamlandi")

    async def check_student_data_protection(self) -> None:
        """Ogrenci Verilerinin Korunmasi (Egitim sektoru spesifik)"""
        print("\n[EGITIM] Ogrenci Veri Koruma Kontrolu...")

        # Ogrenci verileri
        student_data_types = [
            ("sinav_sonuc|exam_result|score|puan", "Sinav sonuclari"),
            ("ogrenme_stili|learning_style", "Ogrenme stili verileri"),
            ("performans|performance|basari", "Performans verileri"),
            ("ogrenci_profil|student_profile", "Ogrenci profili"),
        ]

        for pattern, data_type in student_data_types:
            found_files = []
            for py_file in self.backend_path.rglob("*.py"):
                if "venv" in str(py_file) or "test" in str(py_file).lower():
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                    if re.search(pattern, content):
                        found_files.append(py_file.name)
                except Exception:
                    pass

            if found_files:
                self.report.add_finding(KVKKFinding(
                    article="Egitim Sektoru",
                    requirement=data_type,
                    status=ComplianceStatus.NEEDS_REVIEW,
                    severity=Severity.MEDIUM,
                    description=f"{data_type} isleniyor - KVKK uyumu dogrulanmali",
                    evidence=f"Dosyalar: {', '.join(found_files[:3])}",
                    recommendation="Veri isleme amaci ve suresi belgelenmeli",
                ))

        # Cocuk verisi (18 yas alti)
        minor_patterns = [r"age|yas|birth.*date|dogum.*tarih", r"minor|resin|cocuk"]
        minor_found = False

        for pattern in minor_patterns:
            for py_file in self.backend_path.rglob("*.py"):
                if "venv" in str(py_file):
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                    if re.search(pattern, content):
                        minor_found = True
                        break
                except Exception:
                    pass

        if minor_found:
            self.report.add_finding(KVKKFinding(
                article="Egitim Sektoru",
                requirement="Cocuk verisi korumasi",
                status=ComplianceStatus.NEEDS_REVIEW,
                severity=Severity.CRITICAL,
                description="18 yas alti ogrenci verisi isleniyor",
                recommendation="Veli rizasi mekanizmasi implement edilmeli",
            ))

        print("  [OK] Ogrenci veri koruma kontrolu tamamlandi")

    async def check_audit_logging(self) -> None:
        """Denetim Kayitlari (Audit Logging) Kontrolu"""
        print("\n[AUDIT] Denetim Kayitlari Kontrolu...")

        audit_patterns = [
            (r"audit.*log|log.*audit", "Audit logging modulu"),
            (r"access.*log|login.*log", "Erisim kayitlari"),
            (r"data.*access.*log|veri.*erisim.*log", "Veri erisim kayitlari"),
            (r"change.*log|degisiklik.*log|modification.*log", "Degisiklik kayitlari"),
        ]

        audit_score = 0
        for pattern, feature in audit_patterns:
            found = False
            for py_file in self.backend_path.glob("core/*audit*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                    if re.search(pattern, content):
                        found = True
                        break
                except Exception:
                    pass

            if not found:
                for py_file in self.backend_path.rglob("*.py"):
                    if "venv" in str(py_file):
                        continue
                    try:
                        content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                        if re.search(pattern, content):
                            found = True
                            break
                    except Exception:
                        pass

            status = ComplianceStatus.COMPLIANT if found else ComplianceStatus.NON_COMPLIANT
            self.report.add_finding(KVKKFinding(
                article="Madde 12 - Audit",
                requirement=feature,
                status=status,
                severity=Severity.INFO if found else Severity.MEDIUM,
                description=f"{feature} {'mevcut' if found else 'eksik'}",
            ))

            if found:
                audit_score += 1

        print(f"  [OK] Audit logging kontrolu tamamlandi ({audit_score}/4)")

    async def check_pii_handling(self) -> None:
        """PII (Personally Identifiable Information) Yonetimi"""
        print("\n[PII] Kisisel Veri Yonetimi Kontrolu...")

        pii_fields = [
            (r"email", "E-posta adresi"),
            (r"phone|telefon|gsm", "Telefon numarasi"),
            (r"address|adres", "Adres bilgisi"),
            (r"tc_kimlik|tcno|national_id", "TC Kimlik No"),
            (r"ip_address|ip_adres", "IP adresi"),
        ]

        for pattern, pii_type in pii_fields:
            found_files = []
            encrypted = False

            for py_file in self.backend_path.rglob("*.py"):
                if "venv" in str(py_file) or "test" in str(py_file).lower():
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                    if re.search(pattern, content):
                        found_files.append(py_file.name)
                        if "encrypt" in content or "hash" in content:
                            encrypted = True
                except Exception:
                    pass

            if found_files:
                if encrypted:
                    status = ComplianceStatus.COMPLIANT
                    severity = Severity.INFO
                    desc = f"{pii_type} isleniyor ve sifreleme/hash kullaniliyor"
                else:
                    status = ComplianceStatus.NEEDS_REVIEW
                    severity = Severity.MEDIUM
                    desc = f"{pii_type} isleniyor - sifreleme durumu kontrol edilmeli"

                self.report.add_finding(KVKKFinding(
                    article="PII Yonetimi",
                    requirement=pii_type,
                    status=status,
                    severity=severity,
                    description=desc,
                    evidence=f"Dosyalar: {', '.join(found_files[:3])}",
                ))

        print("  [OK] PII kontrolu tamamlandi")

    def export_report(self, output_path: str) -> None:
        """Raporu JSON ve Markdown olarak kaydet"""
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # JSON
        json_path = output_dir / "kvkk_compliance_report.json"
        report_dict = {
            "scan_date": self.report.scan_date,
            "platform": self.report.platform,
            "summary": self.report.summary,
            "findings": [
                {
                    "article": f.article,
                    "requirement": f.requirement,
                    "status": f.status.value,
                    "severity": f.severity.value,
                    "description": f.description,
                    "file_path": f.file_path,
                    "evidence": f.evidence,
                    "recommendation": f.recommendation,
                }
                for f in self.report.findings
            ],
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        # Markdown
        md_path = output_dir / "KVKK_COMPLIANCE_REPORT.md"
        md_content = self._generate_markdown_report()

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        print("\n[RAPOR] Raporlar olusturuldu:")
        print(f"   - {json_path}")
        print(f"   - {md_path}")

    def _generate_markdown_report(self) -> str:
        """Markdown raporu olustur"""
        summary = self.report.summary

        md = f"""# KIRO2 KVKK Uyumluluk Raporu

**Tarama Tarihi:** {self.report.scan_date}
**Platform:** {self.report.platform}

---

## Yonetici Ozeti

| Metrik | Sayi |
|--------|------|
| Toplam Kontrol | {summary.get('total_checks', 0)} |
| Uyumlu | {summary.get('compliant', 0)} |
| Uyumsuz | {summary.get('non_compliant', 0)} |
| Kismi Uyumlu | {summary.get('partial', 0)} |
| Inceleme Gerekli | {summary.get('needs_review', 0)} |

### Uyumluluk Skoru: **{summary.get('compliance_score', 0)}%**

| Ciddiyet | Sayi |
|----------|------|
| Kritik | {summary.get('critical', 0)} |
| Yuksek | {summary.get('high', 0)} |

---

## Detayli Bulgular

"""
        # Maddeye gore grupla
        articles = {}
        for f in self.report.findings:
            if f.article not in articles:
                articles[f.article] = []
            articles[f.article].append(f)

        for article, findings in articles.items():
            md += f"\n### {article}\n\n"
            for f in findings:
                status_icon = "[UYUMLU]" if f.status == ComplianceStatus.COMPLIANT else "[UYUMSUZ]" if f.status == ComplianceStatus.NON_COMPLIANT else "[KISMI]" if f.status == ComplianceStatus.PARTIAL else "[INCELEME]"
                md += f"""#### {f.requirement} {status_icon}

- **Durum:** {f.status.value}
- **Ciddiyet:** {f.severity.value}
- **Aciklama:** {f.description}
"""
                if f.evidence:
                    md += f"- **Kanit:** {f.evidence}\n"
                if f.recommendation:
                    md += f"- **Oneri:** {f.recommendation}\n"
                md += "\n"

        md += """---

## Oneriler

1. **Acil:** Tum KRITIK ve YUKSEK ciddiyet bulgulari ele alinmali
2. **Kisa Vadeli:** ORTA ciddiyet bulgulari incelenmeli
3. **Uzun Vadeli:** Surdurulebilir KVKK uyumluluk sureci olusturulmali

## Referanslar

- [6698 Sayili KVKK](https://www.mevzuat.gov.tr/MevzuatMetin/1.5.6698.pdf)
- [KVVK Kurul Kararlari](https://www.kvkk.gov.tr/Icerik/5256/Kurul-Kararlari)
- [Kisisel Veri Isleme Envanteri Hazirlanmasi Rehberi](https://www.kvkk.gov.tr/Icerik/4196/Kisisel-Veri-Isleme-Envanteri-Hazirlama-Rehberi)

---

*Rapor KIRO2 KVKK Uyumluluk Tarayicisi tarafindan olusturulmustur*
"""
        return md


async def main():
    """Ana fonksiyon"""
    backend_path = Path(__file__).parent.parent.parent
    frontend_path = backend_path.parent / "frontend"
    output_path = Path(__file__).parent

    scanner = KVKKComplianceScanner(str(backend_path), str(frontend_path))
    report = await scanner.run_full_scan()

    print("\n" + "=" * 60)
    print("[OZET] KVKK DENETIMI TAMAMLANDI")
    print("=" * 60)

    summary = report.summary
    print(f"Toplam Kontrol: {summary['total_checks']}")
    print(f"  Uyumlu: {summary['compliant']}")
    print(f"  Uyumsuz: {summary['non_compliant']}")
    print(f"  Kismi: {summary['partial']}")
    print(f"  Inceleme Gerekli: {summary['needs_review']}")
    print()
    print(f"Uyumluluk Skoru: %{summary['compliance_score']}")
    print()
    print(f"  Kritik: {summary['critical']}")
    print(f"  Yuksek: {summary['high']}")

    scanner.export_report(str(output_path))

    if summary['non_compliant'] > 3 or summary['critical'] > 0:
        print("\n[UYARI] KVKK UYUMLULUK SORUNLARI TESPIT EDILDI!")
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
