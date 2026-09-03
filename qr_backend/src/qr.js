const express = require("express");
const multer = require("multer");

const qrController = require("./qrController");

const router = express.Router();

const upload = multer({
    storage: multer.memoryStorage()
});

router.post(
    "/scan-image",
    upload.single("qrImage"),
    qrController.scanQrImage
);

module.exports = router;