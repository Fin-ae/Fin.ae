import { useState } from "react";
import { products } from "../data/products";

function Compare() {
  const [salary, setSalary] = useState("");
  const [sharia, setSharia] = useState(false);

  const filtered = products.filter((p) => {
    return (
      (salary === "" || p.salary <= salary) &&
      (!sharia || p.sharia === true)
    );
  });

  return (
    <div className="min-h-screen flex">

      {/* Filters */}
      <div className="w-64 p-4 border-r bg-gray-50">
        <h2 className="text-xl font-bold mb-4">Filters</h2>

        <label className="block mb-2">Salary</label>
        <input
          type="number"
          className="border p-2 w-full mb-4"
          onChange={(e) => setSalary(e.target.value)}
        />

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            onChange={(e) => setSharia(e.target.checked)}
          />
          Sharia Compliant
        </label>
      </div>

      {/* Products */}
      <div className="flex-1 p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((p) => (
          <div key={p.id} className="border p-4 rounded shadow">
            <h3 className="text-lg font-bold">{p.name}</h3>
            <p className="text-gray-600">{p.bank}</p>
            <p className="mt-2">{p.benefit}</p>
            <p className="text-sm mt-2">
              Salary Required: {p.salary}
            </p>

            {p.sharia && (
              <span className="text-green-600 text-sm">
                Sharia Compliant
              </span>
            )}

            <button className="mt-3 bg-blue-600 text-white px-4 py-1 rounded">
              Apply
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Compare;
