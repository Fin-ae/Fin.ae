import ProductCard from "../components/ProductCard";
import FilterSidebar from "../components/FilterSidebar";

function Compare() {
  const dummyProducts = [
    { name: "Credit Card A", bank: "Bank A", benefit: "Cashback 5%" },
    { name: "Loan B", bank: "Bank B", benefit: "Low Interest" },
  ];

  return (
    <div style={styles.container}>
      <FilterSidebar />

      <div style={styles.products}>
        {dummyProducts.map((p, i) => (
          <ProductCard key={i} product={p} />
        ))}
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
  },
  products: {
    flex: 1,
    display: "flex",
    gap: "20px",
    padding: "20px",
  },
};

export default Compare;