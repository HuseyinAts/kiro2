"""`scripts/scan_split_accesses.py` göç sayacının davranışını çivileyen testler.

Neden bu alet test ister: #485 göçünde "hangi dosya bitti" sorusunun TEK cevabı
bu script'in çıktısı. Ondan önceki regex sayacı sekiz oturum boyunca yanlıştı
(10 erişim raporluyordu, gerçek 146) ve planlamayı yanlış yönlendirdi. Bir ölçüm
aletinde yanlış-SIFIR en pahalı hatadır: dosya çıktıdan düşer, insan "bitti" der.

Her test bir kusur sınıfına karşılık gelir; hepsi mutasyonla çivilenmiştir
(bkz. dosya sonundaki mutasyon kaydı).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "scan_split_accesses.py"


def _load():
    spec = importlib.util.spec_from_file_location("scan_split_accesses", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scanner = _load()


def _probe(
    tmp_path: Path, src: str, name: str = "probe.py", encoding: str = "utf-8"
) -> Path:
    p = tmp_path / name
    p.write_text(src, encoding=encoding)
    return p


def test_yorum_ve_docstring_erisim_sayilmaz(tmp_path: Path) -> None:
    """Rewrite'ın varlık sebebi: eski regex `osym_exam_engine.py:1327` yorumunu
    "kalan 1 erişim" diye raporluyordu — ölçülmüş fantom."""
    src = '''
"""Docstring icinde QuestionBankItem.irt_difficulty gecerse sayilmamali."""
from models.question_bank import QuestionBankItem

# QuestionBankItem.subject_area is String, not Enum
x = 1
'''
    cls, ent, kws = scanner.scan(_probe(tmp_path, src))
    assert cls == [], f"yorum/docstring erisim sayildi: {cls}"
    assert kws == []


@pytest.mark.parametrize("alias", ["Question", "Soru", "_QB"])
def test_aliasli_import_takip_edilir(tmp_path: Path, alias: str) -> None:
    """Depoda ölçüldü: 15 alias'lı import / 11 dosya. Alias körlüğü 146 SINIF
    erişiminin 138'ini (%94,5) görünmez kılıyordu."""
    src = f"""
from models.question_bank import QuestionBankItem as {alias}

stmt = select({alias}.irt_difficulty)
"""
    cls, ent, kws = scanner.scan(_probe(tmp_path, src))
    assert [c[1] for c in cls] == ["irt_difficulty"], f"alias {alias} takip edilmedi"


def test_parent_kolonu_borc_olarak_sayilmaz(tmp_path: Path) -> None:
    """I4 guard: `is_active` parent'ta duruyor, erişimi GEÇERLİ. Guard olmasaydı
    bir ad çakışmasında 95 geçerli erişim borç gibi raporlanırdı."""
    src = """
from models.question_bank import QuestionBankItem

stmt = select(QuestionBankItem).where(QuestionBankItem.is_active == True)
"""
    cls, ent, kws = scanner.scan(_probe(tmp_path, src))
    assert cls == [], f"parent kolonu borc sayildi: {cls}"
    assert "is_active" not in scanner.SPLIT_FIELDS


def test_id_split_alan_sayilmaz(tmp_path: Path) -> None:
    """`id` paylaşılan PK; her yavru tabloda var. Hariç tutulmasaydı tek başına
    yüzlerce yanlış-pozitif üretirdi."""
    assert "id" not in scanner.SPLIT_FIELDS
    src = """
from models.question_bank import QuestionBankItem

stmt = select(QuestionBankItem).where(QuestionBankItem.id == 5)
"""
    cls, ent, kws = scanner.scan(_probe(tmp_path, src))
    assert cls == []


def test_parse_edilemeyen_dosya_sessizce_yutulmaz(tmp_path: Path) -> None:
    """I3: sessiz `except SyntaxError: return [], []` yanlış-SIFIR üretir —
    dosya çıktıdan tamamen kaybolur ve TOPLAM düşer, bu "iş bitti" gibi okunur."""
    bozuk = _probe(tmp_path, "def broken(:\n    pass\n", name="bozuk.py")
    with pytest.raises(SyntaxError):
        scanner.scan(bozuk)


def test_bom_lu_dosya_hala_taranir(tmp_path: Path) -> None:
    """I3 ikinci yarısı: BOM'lu dosya `utf-8` ile `ast.parse`'ta U+FEFF hatası
    verir. Bu depoda BOM olayı yaşandı (#456); `utf-8-sig` zorunlu."""
    src = """
from models.question_bank import QuestionBankItem

stmt = select(QuestionBankItem.irt_difficulty)
"""
    p = _probe(tmp_path, src, name="bomlu.py", encoding="utf-8-sig")
    assert p.read_bytes().startswith(b"\xef\xbb\xbf"), "fixture BOM tasimiyor"
    cls, ent, kws = scanner.scan(p)
    assert [c[1] for c in cls] == ["irt_difficulty"], "BOM'lu dosya sessizce bos dondu"


def test_update_values_kwarg_sayilir(tmp_path: Path) -> None:
    """C1 regresyon — EN KRİTİK test. `.values(alan=...)` içinde alan adı keyword
    ARGÜMAN ADIdır; AST'de `Attribute` düğümü yoktur, yani SINIF taraması bunu
    yapısal olarak göremez. `core/irt_daemon.py:211` altı taşınmış alanı böyle
    yazıyor → her IRT kalibrasyon yazımı `CompileError`. Bu test olmadan sayaç
    "irt_daemon bitti" diyebilirdi."""
    src = """
from models.question_bank import QuestionBankItem

stmt = (
    update(QuestionBankItem)
    .where(QuestionBankItem.id == 1)
    .values(irt_difficulty=0.5, is_calibrated=True)
)
"""
    cls, ent, kws = scanner.scan(_probe(tmp_path, src))
    assert sorted(k[1] for k in kws) == ["irt_difficulty", "is_calibrated"]
    assert all(k[3] == "values" for k in kws)


def test_db_query_entity_olarak_sayilir(tmp_path: Path) -> None:
    """C2 regresyon: `db.query(X)` `select(X)` ile aynı entity'yi aynı
    lazy='select' riskiyle yükler. Eskiden `difficulty_classification_service.py`
    `ENTITY=0` raporlanıyordu — olgusal olarak yanlış, 2 vardı."""
    src = """
from models.question_bank import QuestionBankItem

q = db.query(QuestionBankItem).filter(QuestionBankItem.id == 1).first()
"""
    cls, ent, kws = scanner.scan(_probe(tmp_path, src))
    assert [(e[1], e[2]) for e in ent] == [("QuestionBankItem", "query")]
