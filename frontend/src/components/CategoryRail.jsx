const ICONS = {
  arithmetic: "±",
  age: "◷",
  emi: "₹",
  statistics: "σ",
  units: "⇄",
};

export default function CategoryRail({ calculators, selected, onSelect }) {
  return (
    <aside className="category-rail" aria-label="Calculator categories">
      <div className="rail-heading">
        <span>Verified tools</span>
        <strong>{calculators.length}</strong>
      </div>
      <button
        className={!selected ? "category-button active" : "category-button"}
        onClick={() => onSelect(null)}
        type="button"
      >
        <span className="category-icon">AI</span>
        <span>
          <strong>Automatic</strong>
          <small>Detect from request</small>
        </span>
      </button>
      {calculators.map((calculator) => (
        <button
          className={selected === calculator.id ? "category-button active" : "category-button"}
          key={calculator.id}
          onClick={() => onSelect(calculator.id)}
          type="button"
        >
          <span className="category-icon">{ICONS[calculator.id] || "∑"}</span>
          <span>
            <strong>{calculator.name}</strong>
            <small>{calculator.description}</small>
          </span>
        </button>
      ))}
    </aside>
  );
}

