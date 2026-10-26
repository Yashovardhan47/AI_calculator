export default function PromptComposer({ query, onQueryChange, onSubmit, loading, examples }) {
  return (
    <section className="composer-panel">
      <div className="composer-label-row">
        <label htmlFor="calculation-query">What should I calculate?</label>
        <span>Natural language or an expression</span>
      </div>
      <form onSubmit={onSubmit}>
        <div className="prompt-box">
          <textarea
            autoFocus
            id="calculation-query"
            maxLength={2000}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Try: standard deviation of 12, 18, 21, 23 and 31"
            rows={4}
            value={query}
          />
          <div className="prompt-footer">
            <span>{query.length}/2000</span>
            <button disabled={loading || !query.trim()} type="submit">
              {loading ? "Calculating…" : "Calculate"}
              {!loading && <span aria-hidden="true">→</span>}
            </button>
          </div>
        </div>
      </form>
      <div className="example-row" aria-label="Example requests">
        {examples.map((example) => (
          <button key={example} onClick={() => onQueryChange(example)} type="button">
            {example}
          </button>
        ))}
      </div>
    </section>
  );
}
