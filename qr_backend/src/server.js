require("dotenv").config();

const express = require("express");
const cors = require("cors");
const path = require("path");
const { spawn } = require("child_process");

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

let controllerProcess = null;


function isControllerRunning() { //python controller calisiyor mu?

    return new Promise((resolve) => {

        const http = require("http");

        const request = http.get(
            "http://127.0.0.1:5050/health",
            (response) => {

                response.resume();

                resolve(true);
            }
        );

        request.on("error", () => {

            resolve(false);
        });

        request.setTimeout(1000, () => {

            request.destroy();

            resolve(false);
        });
    });
}


async function startController() {

    const alreadyRunning = await isControllerRunning();

    if (alreadyRunning) {

        console.log(
            "QR Controller zaten çalışıyor."
        );

        return;
    }

    const controllerPath = path.resolve(
        __dirname,
        "../../qr_controller/main.py"
    );

    console.log(
        "QR Controller başlatılıyor..."
    );

    controllerProcess = spawn(
        "python3",
        [controllerPath],
        {
            cwd: path.dirname(controllerPath),
            stdio: "inherit"
        }
    );

    controllerProcess.on(
        "error",
        (error) => {

            console.error(
                "Controller başlatma hatası:",
                error.message
            );
        }
    );

    controllerProcess.on(
        "exit",
        (code, signal) => {

            console.log(
                `Controller kapandı. code=${code}, signal=${signal}`
            );

            controllerProcess = null;
        }
    );
}


app.listen(
    PORT,
    "0.0.0.0",
    async () => {

        console.log(
            `Backend ${PORT} portunda çalışıyor.`
        );

        await startController();
    }
);


function shutdown() {

    console.log(
        "Backend kapatılıyor..."
    );

    if (controllerProcess) {

        controllerProcess.kill("SIGTERM");
    }

    process.exit(0);
}


process.on(
    "SIGINT",
    shutdown
);

process.on(
    "SIGTERM",
    shutdown
);