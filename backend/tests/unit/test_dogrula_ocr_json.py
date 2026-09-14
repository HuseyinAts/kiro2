"""dogrula_ocr_json.py bekcisinin BILEREK bozulmus girdiyi yakaladigini kanitlar.

Neden test: bu dogrulayici, OCR ciktisini ureten modelin KENDI beyanina
(count_matches) guvenmemek icin var. Kontrolun kendisi sessizce bozulursa
(orn. bir refactor'da kural dususe) ciktilar "temiz" gorunur ve kusur gecer.
En kritik assert K3'tur: yanlis beyan tespiti.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

PIPELINE = Path(__file__).resolve().parents[2] / "scripts" / "pipeline"
sys.path.insert(0, str(PIPELINE))

dogrula_modul = pytest.importorskip(
    "dogrula_ocr_json", reason="pipeline script'i bulunamadi"
)
dogrula = dogrula_modul.dogrula


def _soru(no: int, sutun: str, cevap: str | None = "A") -> dict:
    return {
        "position_on_page": no,
        "column": sutun,
        "question_number_on_page": no,
        "question_text": f"Bu {no}. sorunun yeterince uzun ve gecerli metnidir?",
        "options": {"A": "bir", "B": "iki", "C": "uc", "D": "dort", "E": "bes"},
        "correct_answer": cevap,
    }


def _sayfa(sorular: list[dict], **ek) -> dict:
    d = {
        "file_page": "0001",
        "page_type": "questions",
        "questions": sorular,
        "extracted_question_count": len(sorular),
        "count_matches": True,
        "page_notes": "",
    }
    d.update(ek)
    return d


def _kur(tmp_path: Path, sayfalar: dict[str, dict]) -> Path:
    (tmp_path / "ocr_json").mkdir()
    with (tmp_path / "manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["dosya", "beklenen_soru", "sol_sutun", "sag_sutun", "sayfa_tipi"])
        for ad in sayfalar:
            w.writerow([f"{ad}.png", 3, 2, 1, "soru"])
    for ad, veri in sayfalar.items():
        (tmp_path / "ocr_json" / f"{ad}.json").write_text(
            json.dumps(veri, ensure_ascii=False), encoding="utf-8"
        )
    return tmp_path


def test_temiz_cikti_kusursuz_gecer(tmp_path: Path, capsys) -> None:
    """Kontrol kolu: dogru girdi alarm URETMEMELI (yoksa bekci her seye baginr)."""
    hedef = _kur(
        tmp_path,
        {"sayfa_0001": _sayfa([_soru(1, "sol"), _soru(2, "sol"), _soru(3, "sag")])},
    )
    assert dogrula(hedef) == 0
    assert "KUSUR: 0" in capsys.readouterr().out


def test_yanlis_beyan_yakalanir(tmp_path: Path, capsys) -> None:
    """K3: JSON 'count_matches: true' derken gercekte tutmuyorsa YAKALANMALI."""
    eksik = _sayfa([_soru(1, "sol"), _soru(2, "sol")])  # manifest 3 bekliyor
    assert eksik["count_matches"] is True  # uretici "tuttu" diyor
    hedef = _kur(tmp_path, {"sayfa_0001": eksik})

    assert dogrula(hedef) == 1
    cikti = capsys.readouterr().out
    assert "K1 soru sayisi 2 != manifest 3" in cikti
    assert "YANLIS BEYAN" in cikti


def test_kisaltma_ve_gecersiz_cevap_yakalanir(tmp_path: Path, capsys) -> None:
    """K6 + K4: '...' ile kesilmis metin ve A-E disi cevap sessizce gecmemeli."""
    s = _sayfa([_soru(1, "sol"), _soru(2, "sol"), _soru(3, "sag")])
    s["questions"][0]["question_text"] = "Bu soru metni yarida kesilmistir ve..."
    s["questions"][1]["correct_answer"] = "F"
    hedef = _kur(tmp_path, {"sayfa_0001": s})

    assert dogrula(hedef) == 1
    cikti = capsys.readouterr().out
    assert "K6 kisaltma izi" in cikti
    assert "K4 gecersiz correct_answer='F'" in cikti


def test_ayni_kok_farkli_siklar_tekrar_SAYILMAZ(tmp_path: Path, capsys) -> None:
    """K9/K10 yanlis-pozitif vermemeli: ayni soru koku + FARKLI siklar = FARKLI soru.

    Gercek vaka: "Asagidakilerden hangisi tum canlilarin ortak ozelligi degildir?"
    koku bu kitapta iki ayri soruda geciyor (sayfa_0009 s.8 -> 2018 MSU,
    sayfa_0016 s.1 -> 2025); siklari tamamen farkli. Tekillik anahtari yalniz
    koke bakarsa bu iki gecerli soru 'kopya' diye isaretlenir.
    """
    kok = "Aşağıdakilerden hangisi tüm canlıların ortak özelliği değildir?"
    q1, q2, q3 = _soru(1, "sol"), _soru(2, "sol"), _soru(3, "sag")
    q1["question_text"] = q2["question_text"] = kok
    q1["options"] = {
        "A": "Hücresel yapı",
        "B": "Metabolizma",
        "C": "Oksijenli solunum",
        "D": "Genetik madde",
        "E": "Tepki verme",
    }
    q2["options"] = {
        "A": "Tek hücre",
        "B": "Enerji kullanma",
        "C": "Oksijen kullanma",
        "D": "Uyarıya tepki",
        "E": "Kalıtsal materyal",
    }
    hedef = _kur(tmp_path, {"sayfa_0001": _sayfa([q1, q2, q3])})

    assert dogrula(hedef) == 0
    cikti = capsys.readouterr().out
    assert "K9" not in cikti
    assert "K10" not in cikti


def test_gercek_kopya_yakalanir(tmp_path: Path, capsys) -> None:
    """Kok VE siklar ayniysa bu gercek kopyadir -> yakalanmali."""
    q1, q2, q3 = _soru(1, "sol"), _soru(2, "sol"), _soru(3, "sag")
    q2["question_text"] = q1["question_text"]
    q2["options"] = dict(q1["options"])
    hedef = _kur(tmp_path, {"sayfa_0001": _sayfa([q1, q2, q3])})

    assert dogrula(hedef) == 1
    assert "K9 ayni sayfada TEKRAR eden soru metni" in capsys.readouterr().out


def test_bindirmeden_dogan_tekrar_yakalanir(tmp_path: Path, capsys) -> None:
    """K9: sol/sag kirpiklari 60 px bindirmeli -> ayni soru iki kez yazilabilir."""
    s = _sayfa([_soru(1, "sol"), _soru(1, "sag"), _soru(3, "sag")])
    s["questions"][1]["question_number_on_page"] = 2
    hedef = _kur(tmp_path, {"sayfa_0001": s})

    assert dogrula(hedef) == 1
    assert "K9 ayni sayfada TEKRAR eden soru metni" in capsys.readouterr().out
