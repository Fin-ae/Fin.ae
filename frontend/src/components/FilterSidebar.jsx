function FilterSidebar() {
  return (
    <div style={styles.sidebar}>
      <h3>Filters</h3>

      <label>Salary</label>
      <input type="number" placeholder="Enter salary" />

      <label>Age</label>
      <input type="number" placeholder="Enter age" />

      <label>
        <input type="checkbox" /> Sharia Compliant
      </label>
    </div>
  );
}

const styles = {
  sidebar: {
    width: "250px",
    padding: "20px",
    borderRight: "1px solid #ccc",
  },
};

export default FilterSidebar;
