"""requirements-minimal.txt'e kalan eksik paketleri ekle (2. tur)."""

path = r"C:\Users\husey\kiro2\backend\requirements-minimal.txt"

with open(path, encoding="utf-8") as f:
    existing = f.read()

# Zaten eklenmis olanlari atla
new_pkgs = []

checks = {
    "qrcode": "qrcode[pil]>=7.4.0",
    "openai": "openai>=1.50.0",
    "hijri_converter": "hijri-converter>=2.3.1",
    "matplotlib": "matplotlib>=3.7.0",
    "reportlab": "reportlab>=4.0.0",
    "networkx": "networkx>=3.1",
}

for key, pkg_line in checks.items():
    if key not in existing:
        new_pkgs.append(pkg_line)

# scripts modulu backend/scripts/ klasoru — fixture degil, path sorunu
# Bu icin requirements degil, sys.path duzeltmesi gerekiyor
# Simdilik not olarak birakalim

if new_pkgs:
    additions = "\n# 2. tur eksik paketler (22 Mart 2026)\n" + "\n".join(new_pkgs) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(additions)
    print(f"OK: {len(new_pkgs)} paket eklendi:")
    for p in new_pkgs:
        print(f"  + {p}")
else:
    print("Zaten tum paketler mevcut.")
