#!/bin/bash

PROJECT="/Users/zarashahbazova/Downloads/qrProjesi"

echo "QR projesi başlatılıyor..."

# Backend
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT/qr_backend' && npm run dev\""

# QR Web
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT/qr_web' && python3 app.py\""

# Appium
osascript -e "tell application \"Terminal\" to do script \"appium\""

# QR Appium otomasyonu
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT/qr_appium' && python3 telegram.py\""

# Camera agent
osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT/camera' && python3 agent.py\""


echo "Gerekli servisler başlatıldı."