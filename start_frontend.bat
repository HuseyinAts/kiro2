@echo off
echo 🎨 Teknofest 2025 - Frontend Başlatılıyor...
echo ==========================================
cd frontend
echo 📦 Node.js sürümü:
node --version
echo 📦 NPM sürümü:
npm --version
echo.
echo 🔧 Dependencies kontrol ediliyor...
if not exist node_modules (
    echo 📥 Dependencies yükleniyor...
    npm install
)
echo.
echo 🎨 Frontend başlatılıyor (Port: 3002)...
echo ⚠️  Not: Frontend Port 3002'de çalışacak (vite.config.ts ayarı)
npm run dev
pause