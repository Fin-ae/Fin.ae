import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">

      {/* Navbar */}
      <div className="flex justify-between items-center p-4 bg-blue-900 text-white">
        <h1 className="text-xl font-bold">Fin.ae</h1>

        <div className="space-x-4">
          <button onClick={() => navigate("/")}>Home</button>
          <button onClick={() => navigate("/compare")}>Compare</button>
        </div>
      </div>

      {/* Hero Section */}
      <div className="text-center mt-20 px-4">
        <h2 className="text-4xl font-bold">
          Compare Financial Products in UAE
        </h2>

        <p className="text-gray-600 mt-2">
          Loans, Credit Cards, Insurance & Bank Accounts
        </p>

        <button
          onClick={() => navigate("/compare")}
          className="mt-6 bg-blue-600 text-white px-6 py-2 rounded"
        >
          Start Comparing
        </button>
      </div>

      {/* Categories */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 px-10 mt-16">
        {["Credit Cards", "Loans", "Insurance", "Accounts"].map((item) => (
          <div
            key={item}
            className="bg-white p-6 shadow rounded text-center hover:shadow-lg"
          >
            {item}
          </div>
        ))}
      </div>

    </div>
  );
}

export default Home;