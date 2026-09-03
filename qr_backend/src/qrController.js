const scanQrImage = async (req, res) => {
    try {
        if (!req.file || !req.file.buffer) {
            return res.status(400).json({
                success: false,
                message: "QR görüntüsü gönderilmedi"
            });
        }

        console.log("================================");
        console.log("QR GÖRÜNTÜSÜ TELEFONDAN GELDİ");
        console.log("Boyut:", req.file.size, "bytes");
        console.log("Tip:", req.file.mimetype);
        console.log("================================");

        try {
            const formData = new FormData();

            const imageBlob = new Blob(
                [req.file.buffer],
                {
                    type: req.file.mimetype || "image/jpeg"
                }
            );

            formData.append(
                "qrImage",
                imageBlob,
                req.file.originalname || "qr_capture.jpg"
            );

            const controllerResponse = await fetch(
                "http://127.0.0.1:5050/qr",
                {
                    method: "POST",
                    body: formData
                }
            );

            const controllerText = await controllerResponse.text();

            console.log(
                "QR görüntüsü controller'a gönderildi:",
                controllerResponse.status,
                controllerText
            );

            if (!controllerResponse.ok) {
                return res.status(502).json({
                    success: false,
                    message: "Controller görüntüyü kabul etmedi"
                });
            }

        } catch (error) {
            console.error(
                "QR controller bağlantı hatası:",
                error.message
            );

            return res.status(502).json({
                success: false,
                message: "Controller'a bağlanılamadı"
            });
        }

        return res.status(200).json({
            success: true,
            message:
                "QR görüntüsü backend tarafından alındı ve controller'a gönderildi"
        });

    } catch (error) {
        console.error("QR image error:", error);

        return res.status(500).json({
            success: false,
            message: "Sunucu hatası"
        });
    }
};


module.exports = {
    scanQrImage
};