import { useState } from "react";


function shortHash(value) {
  if (!value) return "Unavailable";
  return `${value.slice(0, 12)}…${value.slice(-8)}`;
}


export default function CalcGraphPanel({ graph, verification, receipt }) {
  const [open, setOpen] = useState(true);

  if (!graph || !verification || !receipt) return null;

  function downloadReceipt() {
    const payload = JSON.stringify({ calcgraph: graph, verification, receipt }, null, 2);
    const url = URL.createObjectURL(new Blob([payload], { type: "application/json" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `calcgraph-${graph.graph_id}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="calcgraph-panel">
      <button className="calcgraph-toggle" type="button" onClick={() => setOpen((value) => !value)} aria-expanded={open}>
        <span>
          <small>Research execution trace</small>
          <strong>CalcGraph · {graph.nodes.length} typed nodes</strong>
        </span>
        <span className={verification.valid ? "graph-valid" : "graph-invalid"}>
          {verification.valid ? "Verified" : "Rejected"} {open ? "−" : "+"}
        </span>
      </button>

      {open && (
        <div className="calcgraph-body">
          <div className="graph-flow" role="list" aria-label="Calculation graph nodes">
            {verification.topological_order.map((nodeId, index) => {
              const node = graph.nodes.find((item) => item.id === nodeId);
              if (!node) return null;
              return (
                <div className="graph-step" role="listitem" key={node.id}>
                  {index > 0 && <span className="graph-arrow" aria-hidden="true">→</span>}
                  <article className={`graph-node ${node.kind}`}>
                    <span>{node.kind}</span>
                    <strong>{node.label}</strong>
                    <code>{node.semantic_type}{node.unit ? ` · ${node.unit}` : ""}</code>
                    {node.operation && <small>{node.operation}</small>}
                  </article>
                </div>
              );
            })}
          </div>

          <div className="verification-grid">
            <div>
              <span>Static verification</span>
              <strong>{receipt.verification_summary.checks_passed} checks passed</strong>
            </div>
            <div>
              <span>Graph fingerprint</span>
              <code title={receipt.graph_fingerprint}>{shortHash(receipt.graph_fingerprint)}</code>
            </div>
            <div>
              <span>Reproducibility hash</span>
              <code title={receipt.reproducibility_hash}>{shortHash(receipt.reproducibility_hash)}</code>
            </div>
          </div>

          <details className="check-list">
            <summary>Inspect verification evidence</summary>
            <ul>
              {verification.checks.map((check, index) => (
                <li key={`${check.id}-${check.node_id || "graph"}-${index}`}>
                  <span className={check.status}>{check.status === "pass" ? "✓" : "×"}</span>
                  <code>{check.id}</code>
                  <p>{check.message}</p>
                </li>
              ))}
            </ul>
          </details>

          <button className="receipt-download" type="button" onClick={downloadReceipt}>Download evidence receipt</button>
        </div>
      )}
    </section>
  );
}
