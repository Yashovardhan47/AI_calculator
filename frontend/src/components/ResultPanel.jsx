export default function ResultPanel({ result, error, loading }) {
  if (loading) {
    return (
      <section className="result-panel result-loading" aria-live="polite">
        <div className="skeleton short" />
        <div className="skeleton answer" />
        <div className="skeleton" />
        <div className="skeleton" />
      </section>
    );
  }

  if (error) {
    return (
      <section className="result-panel result-error" aria-live="polite">
        <span className="state-icon">!</span>
        <div>
          <p>More information is needed</p>
          <strong>{error}</strong>
        </div>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="result-panel result-empty">
        <div className="empty-orbit" aria-hidden="true"><span>∑</span></div>
        <h2>Your verified result will appear here</h2>
        <p>The calculation engine will show the answer, formula, steps, units, and assumptions.</p>
      </section>
    );
  }

  return (
    <section className="result-panel" aria-live="polite">
      <div className="result-heading">
        <div>
          <span className="eyebrow">{result.calculator} calculator</span>
          <h2>{result.title}</h2>
        </div>
        <span className="confidence">{Math.round(result.confidence * 100)}% verified</span>
      </div>

      <div className="answer-card">
        <span>Answer</span>
        <strong>{result.answer}</strong>
      </div>

      <div className="result-section formula-box">
        <span>Formula</span>
        <code>{result.formula}</code>
      </div>

      <div className="result-section">
        <span>Calculation steps</span>
        <ol>
          {result.steps.map((step) => <li key={step}>{step}</li>)}
        </ol>
      </div>

      <div className="assumption-row">
        <span>Assumptions</span>
        <ul>
          {result.assumptions.map((assumption) => <li key={assumption}>{assumption}</li>)}
        </ul>
      </div>
    </section>
  );
}

