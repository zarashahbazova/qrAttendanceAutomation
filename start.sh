#!/bin/bash

echo "🚀 Proje başlatılıyor..."

PROJECT="/Users/zarashahbazova/Downloads/qrProjesi"

# 1. Appium
cd "$PROJECT/qr_appium"
appium &

# 2. Backend
cd "$PROJECT/qr_backend"
npm run dev &

# 3. QR Web / Python
cd "$PROJECT/qr_web"
python3 app.py &

# 4. Telegram + Screenshot
cd "$PROJECT/qr_appium"
python3 telegram_appium.py &

wait