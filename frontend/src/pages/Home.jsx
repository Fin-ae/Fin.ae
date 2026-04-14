import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();

  return (
    <div style={styles.container}>
      <h1>Compare Financial Products in UAE</h1>
      <p>Loans, Credit Cards, Insurance & More</p>

      <button onClick={() => navigate("/compare")} style={styles.button}>
        Start Comparing
      </button>

      <div style={styles.categories}>
        {["Credit Cards", "Loans", "Insurance", "Bank Accounts"].map((item) => (
          <div key={item} style={styles.card}>
            <h3>{item}</h3>
          </div>
        ))}
      </div>

      <div style={styles.aiBox}>
        <h3>Ask AI Assistant</h3>
        <input placeholder="e.g. Best credit card for salary 5000 AED" />
      </div>
    </div>
  );
}

const styles = {
  container: {
    textAlign: "center",
    padding: "40px",
  },
  button: {
    padding: "10px 20px",
    margin: "20px",
    background: "#007bff",
    color: "white",
    border: "none",
  },
  categories: {
    display: "flex",
    justifyContent: "center",
    gap: "20px",
    marginTop: "30px",
  },
  card: {
    padding: "20px",
    border: "1px solid #ccc",
    width: "150px",
  },
  aiBox: {
    marginTop: "40px",
  },
};

export default Home;