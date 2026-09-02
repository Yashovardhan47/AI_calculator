export default function HistoryPanel({ items, onSelect, onClear }) {
  return (
    <section className="history-panel">
      <div className="history-heading">
        <div>
          <span>Recent calculations</span>
          <small>Stored only on this device</small>
        </div>
        {items.length > 0 && <button onClick={onClear} type="button">Clear</button>}
      </div>
      {items.length === 0 ? (
        <p className="history-empty">Completed calculations will be saved here.</p>
      ) : (
        <div className="history-list">
          {items.map((item) => (
            <button key={item.request_id} onClick={() => onSelect(item)} type="button">
              <span>{item.calculator}</span>
              <strong>{item.query}</strong>
              <small>{item.answer}</small>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

