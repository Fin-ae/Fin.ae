// backend/server.js
const express = require("express");
const cors = require("cors");
const app = express();

app.use(cors());

const products = [
  { id: 1, name: "Platinum Credit Card", bank: "ENBD", annual_fee: 0, salary: 12000, cashback: 1, sharia: false, interest_rate: 3.25 },
  { id: 2, name: "TouchPoints Infinite", bank: "ADCB", annual_fee: 1050, salary: 30000, cashback: 2, sharia: false, interest_rate: 3.69 },
  { id: 3, name: "Platinum Plus", bank: "Mashreq", annual_fee: 313.95, salary: 10000, cashback: 2, sharia: false, interest_rate: 3.85 },
  { id: 4, name: "Elevate Credit Card", bank: "RAKBANK", annual_fee: 209, salary: 35000, cashback: 3, sharia: false, interest_rate: 3.65 },
  { id: 5, name: "SHAMS Infinite Covered Card", bank: "DIB", annual_fee: 699, salary: 30000, cashback: 3, sharia: true, interest_rate: 0 },
  { id: 6, name: "FAB Z Credit Card", bank: "FAB", annual_fee: 100, salary: 5000, cashback: 1, sharia: false, interest_rate: 1.99 }
];

app.get("/", (req, res) => res.send("API is working"));
app.get("/products", (req, res) => res.json(products));

const PORT = 3000;
app.listen(PORT, () => console.log(`Backend running on http://localhost:${PORT}`));

