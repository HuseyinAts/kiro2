# PDF OLUSTURMA KOMUTLARI
# Yeni PowerShell penceresinde calistir

# Dizini degistir
cd C:\Users\husey\kiro2

# KOMUT 1: Basit PDF (En hizli)
pandoc MASTER_PLAN_11_WEEKS_COMPLETE.md -o MASTER_PLAN_BASIT.pdf

# KOMUT 2: Icindekiler + Numaralama (Onerilen)
pandoc MASTER_PLAN_11_WEEKS_COMPLETE.md -o MASTER_PLAN.pdf --toc --number-sections -V geometry:margin=1in

# KOMUT 3: Profesyonel (XeLaTeX gerekli)
pandoc MASTER_PLAN_11_WEEKS_COMPLETE.md -o MASTER_PLAN_PRO.pdf --pdf-engine=xelatex -V geometry:margin=1in -V fontsize=11pt -V mainfont="Arial" --toc --toc-depth=3 --number-sections

# KOMUT 4: Teknofest Sunumu icin (En iyi)
pandoc MASTER_PLAN_11_WEEKS_COMPLETE.md -o TEKNOFEST_2025_MASTER_PLAN.pdf --pdf-engine=xelatex -V geometry:margin=0.8in -V fontsize=11pt -V mainfont="Calibri" -V colorlinks=true -V linkcolor=blue --toc --toc-depth=3 --number-sections --highlight-style=tango

# Kontrol
dir *.pdf
