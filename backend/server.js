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

const news = [
  {
    id: "news-001",
    title: "UAE Central Bank leaves rates unchanged amid global uncertainty",
    summary: "The Central Bank of the UAE confirmed its decision to keep benchmark rates stable amid global economic uncertainty.",
    source: "Gulf News",
    category: "monetary_policy",
    date: "2026-04-23",
    url: "https://gulfnews.com/uae-central-bank-rates",
    relevance_score: 0.92,
    keywords: ["UAE Central Bank", "rates", "monetary policy"],
  },
  {
    id: "news-002",
    title: "Dubai property market records strong leasing demand",
    summary: "Leasing activity is rising in Dubai as economic stimulus and visa reforms drive investor interest.",
    source: "The National",
    category: "real_estate",
    date: "2026-04-22",
    url: "https://thenational.ae/dubai-property-leasing",
    relevance_score: 0.89,
    keywords: ["Dubai", "real estate", "leasing"],
  },
  {
    id: "news-003",
    title: "UAE insurance premiums show a rebound in health and motor lines",
    summary: "Insurers in the UAE reported premium growth driven by higher demand for health and motor coverage.",
    source: "Insurance Business ME",
    category: "insurance",
    date: "2026-04-21",
    url: "https://insurancebusinessme.com/uae-premiums-growth",
    relevance_score: 0.86,
    keywords: ["insurance", "health insurance", "motor insurance"],
  },
];

app.get("/", (req, res) => res.send("API is working"));
app.get("/products", (req, res) => res.json(products));
app.get("/news", (req, res) => res.json(news));

const PORT = 3000;
app.listen(PORT, () => console.log(`Backend running on http://localhost:${PORT}`));




