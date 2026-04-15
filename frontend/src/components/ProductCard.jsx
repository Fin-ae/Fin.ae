// frontend/src/components/ProductCard.jsx
function ProductCard({ product, onSelect, isSelected, isDisabled, isBest }) {
  return (
    <div
      onClick={() => !isDisabled && onSelect(product)}
      className={`p-4 rounded shadow transition ${
        isSelected
          ? "bg-blue-100 border border-blue-500"
          : isDisabled
          ? "bg-gray-200 cursor-not-allowed opacity-60"
          : "bg-white cursor-pointer hover:shadow-md"
      }`}
    >
      <h3 className="text-xl font-bold flex justify-between items-center">
        {product.name}
        {isBest && (
          <span className="text-xs bg-green-200 px-2 py-1 rounded">Best</span>
        )}
      </h3>
      <p className="text-gray-600">{product.bank}</p>
      <p>💰 Annual Fee: {product.annual_fee}</p>
      <p>💳 Cashback: {product.cashback}%</p>
      <p>📊 Interest Rate: {product.interest_rate}%</p>
      <p>{product.sharia ? "🟢 Sharia Compliant" : "🔴 Conventional"}</p>
    </div>
  );
}

export default ProductCard;


