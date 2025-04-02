const express = require("express");
const app = express();
const port = process.env.PORT || 3000;

// Тестовый файл для загрузки
app.get("/testfile.bin", (req, res) => {
    const fileSize = 10 * 1024 * 1024; // 10 МБ
    res.setHeader("Content-Length", fileSize);
    res.setHeader("Content-Disposition", "attachment; filename=testfile.bin");
    res.send(Buffer.alloc(fileSize));
});

// Эндпоинт для пинга
app.head("/ping", (req, res) => {
    res.status(200).send();
});

// Эндпоинт для теста выгрузки
app.post("/upload", (req, res) => {
    let data = [];
    req.on("data", chunk => data.push(chunk));
    req.on("end", () => {
        res.status(200).send("Upload complete");
    });
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
