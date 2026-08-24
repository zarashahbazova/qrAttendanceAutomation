const { Pool } = require("pg"); //postgresql kütüphanesi

const pool = new Pool({ //database bilgilerini .envden aliyo
    host: process.env.DB_HOST,
    port: process.env.DB_PORT,
    database: process.env.DB_NAME,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
});

pool.on("connect", () => {
    console.log("PostgreSQL bağlantısı başarılı.");
});

pool.on("error", (error) => {
    console.error("PostgreSQL hatası:", error);
});

module.exports = pool; //bu database bağlantısını başka js dosyaları da kullanabilsin