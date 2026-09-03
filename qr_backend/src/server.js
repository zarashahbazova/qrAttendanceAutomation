require("dotenv").config();

const express = require("express");
const cors = require("cors");

const qrRoutes = require("./qr");

const app = express();

app.use(cors());
app.use(express.json());

app.use("/qr", qrRoutes);

app.get("/", (req, res) => {
    res.json({
        message: "QR Yoklama Backend çalışıyor."
    });
});

const PORT = process.env.PORT || 5001;

app.listen(PORT, "0.0.0.0", () => {
    console.log(`Backend ${PORT} portunda çalışıyor.`);
});