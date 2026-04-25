// frontend/src/pages/Compare.jsx
import { useState, useEffect } from "react";
import ProductCard from "../components/ProductCard";

function Compare() {
  const [products, setProducts] = useState([]);
  const [salary, setSalary] = useState("");
  const [shariaOnly, setShariaOnly] = useState(false);
  const [selected, setSelected] = useState([]);
  const [sortBy, setSortBy] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("http://localhost:3000/products")
      .then((res) => res.json())
      .then((data) => { setProducts(data); setLoading(false); })
      .catch(() => { setError("Something went wrong"); setLoading(false); });
  }, []);

  if (loading) return <p className="text-center mt-10">Loading...</p>;
  if (error) return <p className="text-center text-red-500 mt-10">{error}</p>;

  const filtered = products
    .filter(p => (!salary || p.salary <= Number(salary)) && (!shariaOnly || p.sharia))
    .sort((a,b) => sortBy==="cashback"?b.cashback-a.cashback:sortBy==="salary"?a.salary-b.salary:0);

  const best = filtered.length ? filtered.reduce((b,c)=>c.cashback>b.cashback?c:b) : null;

  const handleSelect = (p) => {
    setSelected(prev => {
      const exists = prev.find(s=>s.id===p.id);
      if(exists) return prev.filter(s=>s.id!==p.id);
      if(prev.length<2) return [...prev,p];
      alert("You can compare only 2 products");
      return prev;
    });
  };

  return (
    <div className="p-6 min-h-screen bg-gray-50">
      <h1 className="text-3xl font-bold text-center mb-6">Compare Financial Products</h1>

      {selected.length>0 && <button onClick={()=>setSelected([])} className="block mx-auto mb-4 px-4 py-2 bg-red-500 text-white rounded">Clear Selection</button>}

      <div className="bg-white p-4 rounded shadow max-w-md mx-auto mb-6">
        <input type="number" placeholder="Enter salary" value={salary} onChange={e=>setSalary(e.target.value)} className="border p-2 w-full mb-4 rounded"/>
        <label className="flex items-center gap-2 mb-4">
          <input type="checkbox" checked={shariaOnly} onChange={()=>setShariaOnly(!shariaOnly)} /> Sharia-compliant only
        </label>
        <select value={sortBy} onChange={e=>setSortBy(e.target.value)} className="border p-2 w-full rounded">
          <option value="">Sort By</option>
          <option value="cashback">Highest Cashback</option>
          <option value="salary">Lowest Salary</option>
        </select>
      </div>

      {filtered.length===0 && <p className="text-center text-gray-500 mb-6">No products match your criteria.</p>}

      <div className="grid md:grid-cols-2 gap-4 mb-10">
        {filtered.map(p=>(
          <ProductCard
            key={p.id}
            product={p}
            onSelect={handleSelect}
            isSelected={selected.find(s=>s.id===p.id)}
            isDisabled={selected.length===2 && !selected.find(s=>s.id===p.id)}
            isBest={best?.id===p.id}
          />
        ))}
      </div>

      {selected.length > 0 && (
        <div className="bg-white p-6 rounded shadow max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-4">Comparison</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {selected.map(p => (
              <div key={p.id} className="border p-4 rounded">
                <h3 className="text-xl font-bold">{p.name}</h3>
                <p className="text-gray-600">{p.bank}</p>
                <p>💰 Annual Fee: {p.annual_fee}</p>
                <p>💳 Cashback: {p.cashback}%</p>
                <p>📊 Interest Rate: {p.interest_rate}%</p>
                <p>💼 Min Salary: {p.salary}</p>
                <p>{p.sharia ? "🟢 Sharia Compliant" : "🔴 Conventional"}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Compare;


