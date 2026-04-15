// frontend/src/pages/Home.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import AIAssistant from "../components/AIAssistant";

class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { hasError: false }; }
  static getDerivedStateFromError() { return { hasError: true }; }
  render() {
    if (this.state.hasError)
      return <div className="text-red-500 text-center mt-10">AI Assistant failed to load</div>;
    return this.props.children;
  }
}

function Home() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex justify-between items-center p-4 bg-blue-900 text-white">
        <h1 className="text-xl font-bold">Fin.ae</h1>
        <div className="space-x-4">
          <button onClick={() => navigate("/")}>Home</button>
          <button onClick={() => navigate("/compare")}>Compare</button>
        </div>
      </div>
      <div className="text-center mt-20 px-4">
        <h2 className="text-4xl font-bold">Compare Financial Products in UAE</h2>
        <p className="text-gray-600 mt-2">Loans, Credit Cards, Insurance & Bank Accounts</p>
        <button onClick={() => navigate("/compare")} className="mt-6 bg-blue-600 text-white px-6 py-2 rounded">
          Start Comparing
        </button>
      </div>
      <div className="flex justify-center mt-16 px-4">
        <ErrorBoundary>
          <AIAssistant />
        </ErrorBoundary>
      </div>
    </div>
  );
}

export default Home;

