# MANUEL PDF OLUSTURMA KOMUTU
# Yeni PowerShell penceresinde calistir

# 1. Dizine git
cd C:\Users\husey\kiro2

# 2. Pandoc'u kontrol et
Write-Host "Pandoc kontrol ediliyor..." -ForegroundColor Yellow
pandoc --version

# Eger hata verirse:
# - PowerShell'i kapat ve yeniden ac
# - Bilgisayari yeniden baslat
# - Veya Secenerek 3'e gec

# 3. PDF olustur (Pandoc calisiyor)
Write-Host "`nPDF olusturuluyor..." -ForegroundColor Yellow
pandoc MASTER_PLAN_11_WEEKS_COMPLETE.md -o MASTER_PLAN.pdf

# 4. Kontrol
if (Test-Path "MASTER_PLAN.pdf") {
    Write-Host "`n✅ BASARILI! PDF olusturuldu!" -ForegroundColor Green
    Get-Item "MASTER_PLAN.pdf" | Format-List Name, Length, LastWriteTime
} else {
    Write-Host "`n❌ PDF olusturulamadi!" -ForegroundColor Red
}
