function ProductCard({ product }) {
  return (
    <div style={styles.card}>
      <h3>{product.name}</h3>
      <p>{product.bank}</p>
      <p>{product.benefit}</p>
      <button>View Details</button>
    </div>
  );
}

const styles = {
  card: {
    border: "1px solid #ddd",
    padding: "15px",
    width: "200px",
  },
};

export default ProductCard;
