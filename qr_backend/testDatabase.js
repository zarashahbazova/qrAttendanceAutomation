require("dotenv").config();

const pool = require("./src/config/database");

async function testDatabase() {

    try {

        const result = await pool.query(
            "SELECT NOW()"
        );

        console.log(
            "Database bağlantısı başarılı:"
        );

        console.log(result.rows[0]);

    } catch (error) {

        console.error(
            "Database bağlantı hatası:",
            error
        );

    } finally {

        await pool.end();

    }

}

testDatabase();