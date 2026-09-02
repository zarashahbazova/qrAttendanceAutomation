const express = require("express");

const qrController = require("../qrController");

const router = express.Router();

router.post("/scan", qrController.scanQr);

module.exports = router;