const scanQr = async (req, res) => {
    try {
        const { qrData } = req.body;

        if (!qrData) {
            return res.status(400).json({
                success: false,
                message: "QR verisi gönderilmedi"
            });
        }

        console.log("================================");
        console.log("QR TELEFONDAN GELDİ");
        console.log("QR:", qrData);
        console.log("================================");

        try {
            await fetch("http://127.0.0.1:5050/qr", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    qrData: qrData
                })
            });

            console.log("QR controller'a gönderildi.");

        } catch (error) {
            console.error("QR controller bağlantı hatası:", error.message);
        }

        return res.status(200).json({
            success: true,
            message: "QR backend tarafından alındı",
            qrData: qrData
        });

    } catch (error) {
        console.error("QR scan error:", error);

        return res.status(500).json({
            success: false,
            message: "Sunucu hatası"
        });
    }
};

module.exports = {
    scanQr
};