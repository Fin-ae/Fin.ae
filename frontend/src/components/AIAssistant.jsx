// frontend/src/components/AIAssistant.jsx
import { useState, useEffect } from "react";

function AIAssistant() {
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hi! Ask me about financial products in UAE 🇦🇪" },
  ]);
  const [input, setInput] = useState([]);
  const [products, setProducts] = useState([]);

  useEffect(() => {
    fetch("http://localhost:3000/products")
      .then((res) => res.json())
      .then((data) => setProducts(data))
      .catch(() =>
        setMessages((prev) => [
          ...prev,
          { role: "bot", text: "Failed to load products" },
        ])
      );
  }, []);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    const userMsg = { role: "user", text: trimmed };
    let reply = "Sorry, I don't understand that yet.";
    const lower = trimmed.toLowerCase();

    if (lower.includes("salary")) {
      const match = trimmed.match(/\d+/);
      const salary = match ? Number(match[0]) : null;
      if (salary) {
        const recommended = products
          .filter((p) => p.salary <= salary)
          .sort((a, b) => b.cashback - a.cashback)[0];
        reply = recommended
          ? `You may qualify for: ${recommended.name} (${recommended.bank})`
          : "No matching product found for your salary.";
      } else {
        reply = "Please mention your salary like: 'salary 10000'";
      }
    } else if (lower.includes("credit card")) {
      const best = [...products].sort((a, b) => b.cashback - a.cashback)[0];
      reply = `Top card: ${best.name} from ${best.bank} with ${best.cashback}% cashback`;
    }

    setMessages((prev) => [...prev, userMsg, { role: "bot", text: reply }]);
    setInput("");
  };

  return (
    <div className="border rounded p-4 w-full max-w-md bg-white shadow">
      <h2 className="font-bold mb-2">AI Assistant</h2>
      <div className="h-64 overflow-y-auto border p-2 mb-2 bg-gray-50">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`mb-2 ${m.role === "user" ? "text-right" : "text-left"}`}
          >
            <span
              className={`px-2 py-1 rounded inline-block ${
                m.role === "user" ? "bg-blue-600 text-white" : "bg-gray-300"
              }`}
            >
              {m.text}
            </span>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          className="border p-2 flex-1"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Try: salary 10000"
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button
          onClick={handleSend}
          className="bg-blue-600 text-white px-3 rounded"
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default AIAssistant;

