import { Link } from "react-router-dom";

function Navbar() {
  return (
    <nav style={styles.nav}>
      <h2>Fin.ae</h2>
      <div>
        <Link to="/" style={styles.link}>Home</Link>
        <Link to="/compare" style={styles.link}>Compare</Link>
      </div>
    </nav>
  );
}

const styles = {
  nav: {
    display: "flex",
    justifyContent: "space-between",
    padding: "15px",
    background: "#0a2540",
    color: "white",
  },
  link: {
    marginLeft: "15px",
    color: "white",
    textDecoration: "none",
  },
};

export default Navbar;
