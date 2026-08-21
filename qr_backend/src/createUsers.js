require("dotenv").config();

const bcrypt = require("bcryptjs");
const pool = require("./config/database");

async function createUsers() {

    try {

        const users = [
            {
                number: "9999",
                password: "1234",
                name: "Öğretmen",
                role: "teacher"
            },
            {
                number: "1001",
                password: "1111",
                name: "Zarife Şahbaz",
                role: "student"
            },
            {
                number: "1002",
                password: "2222",
                name: "Emre Kurtuluş",
                role: "student"
            },
            {
                number: "1003",
                password: "3333",
                name: "Şevval Bahtiyar",
                role: "student"
            },
            {
                number: "1004",
                password: "4444",
                name: "Beyza Aydın",
                role: "student"
            },
            {
                number: "1005",
                password: "5555",
                name: "Damla Günendi",
                role: "student"
            }
        ];

        for (const user of users) {

            const passwordHash =
                await bcrypt.hash(user.password, 10);

            await pool.query(
                `
                INSERT INTO users
                (
                    student_number,
                    password_hash,
                    full_name,
                    role
                )
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (student_number)
                DO NOTHING
                `,
                [
                    user.number,
                    passwordHash,
                    user.name,
                    user.role
                ]
            );
        }

        console.log("Kullanıcılar oluşturuldu.");

    } catch (error) {

        console.error(
            "Kullanıcı oluşturma hatası:",
            error
        );

    } finally {

        await pool.end();

    }
}

createUsers();