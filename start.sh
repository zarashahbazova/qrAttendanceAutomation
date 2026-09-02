#!/bin/bash

PROJECT="/Users/zarashahbazova/Downloads/qrProjesi"

echo "QR projesi başlatılıyor..."

# Backend
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT/qr_backend' && npm run dev\""

# Appium
osascript -e "tell application \"Terminal\" to do script \"appium\""

# QR Web
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT/qr_web' && python3 app.py\""

# QR Appium otomasyonu
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT/qr_appium' && python3 telegram.py\""

# Camera agent
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT/qr_camera' && python3 agent.py\""

osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT/qr_app'\""

osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT/qr_app'\""

osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT/qr_apk' && flutter run -d macos\""

echo "Gerekli servisler başlatıldı."