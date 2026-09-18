export default function HistoryPanel({ items, onSelect, onClear, workflows, onRunWorkflow, onDeleteWorkflow }) {
  return (
    <section className="history-panel">
      <div className="history-heading">
        <div>
          <span>Recent calculations</span>
          <small>Synced to your secure workspace</small>
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

      <div className="workflow-heading">
        <span>Saved workflows</span>
        <small>Reusable verified goals</small>
      </div>
      {workflows.length === 0 ? (
        <p className="history-empty">Save a result to rerun its calculation goal later.</p>
      ) : (
        <div className="workflow-list">
          {workflows.map((workflow) => (
            <article key={workflow.id}>
              <button onClick={() => onRunWorkflow(workflow)} type="button">
                <span>Workflow · v{workflow.version}</span>
                <strong>{workflow.name}</strong>
                <small>{workflow.description}</small>
              </button>
              <button aria-label={`Delete ${workflow.name}`} className="workflow-delete" onClick={() => onDeleteWorkflow(workflow.id)} type="button">×</button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
