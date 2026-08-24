const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const pool = require("../config/database");

async function login(req, res) {

    try {

        const {
            student_number,
            password
        } = req.body;


        if (!student_number || !password) {

            return res.status(400).json({
                message: "Numara ve şifre gerekli."
            });

        }


        const result = await pool.query(
            `
            SELECT
                id,
                student_number,
                password_hash,
                full_name,
                role
            FROM users
            WHERE student_number = $1
            `,
            [student_number]
        );


        if (result.rows.length === 0) {

            return res.status(401).json({
                message: "Numara veya şifre hatalı."
            });

        }

        const user = result.rows[0]; //kullanici bilgilerini aliyo

        const passwordCorrect =
            await bcrypt.compare(
                password,
                user.password_hash
            ); //sifre kontrolü

        if (!passwordCorrect) {

            return res.status(401).json({
                message: "Numara veya şifre hatalı."
            });

        }

        const token = jwt.sign( //login basarliysa jwt olusuturluyo
            {
                userId: user.id,
                role: user.role
            },
            process.env.JWT_SECRET
        );


        res.json({ //fluttera gönderiyo token ve bilgileri

            message: "Giriş başarılı.",

            token,

            user: {
                id: user.id,
                student_number: user.student_number,
                full_name: user.full_name,
                role: user.role
            }

        });

    } catch (error) { 

        console.error(error);

        res.status(500).json({
            message: "Sunucu hatası."
        });

    }
}


module.exports = {
    login
};