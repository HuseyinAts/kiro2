"""
Download sample PDFs from ÖSYM to test improved answer key extraction
"""
import requests
from pathlib import Path

# URLs we found from research
pdf_urls = {
    # 2024 YKS (recent, should have clear format)
    "2024_tyt": "https://dokuman.osym.gov.tr/pdfdokuman/2024/YKS/TSK/yks_tyt_2024_kitapcik_T24kt.pdf",
    "2024_ayt": "https://dokuman.osym.gov.tr/pdfdokuman/2024/YKS/TSK/yks_ayt_2024_kitapcik_ts85k.pdf",
    # 2021 YKS (older format)
    "2021_tyt": "http://dokuman.osym.gov.tr/pdfdokuman/2021/YKS/TSK/tyt_yks_2021.pdf",
    "2021_ayt": "http://dokuman.osym.gov.tr/pdfdokuman/2021/YKS/TSK/ayt_yks_2021.pdf",
    # 2013 YGS (even older)
    "2013_ygs": "http://dokuman.osym.gov.tr/pdfdokuman/2013/OSYS/24.03.2013 YGS.pdf",
}

output_dir = Path("test_pdfs")
output_dir.mkdir(exist_ok=True)

print("Downloading sample PDFs from ÖSYM...")
print("=" * 80)

for name, url in pdf_urls.items():
    output_path = output_dir / f"{name}.pdf"

    if output_path.exists():
        print(f"[SKIP] {name} already exists")
        continue

    print(f"[DOWNLOAD] {name}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        size_mb = len(response.content) / (1024 * 1024)
        print(f"[OK] {name} - {size_mb:.2f} MB")
    except Exception as e:
        print(f"[ERROR] {name} - {e}")

print("\n" + "=" * 80)
print("Download complete!")
print(f"PDFs saved to: {output_dir.absolute()}")
