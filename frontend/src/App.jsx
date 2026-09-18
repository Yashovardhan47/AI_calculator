import { useEffect, useMemo, useState } from "react";

import { calculate, clearRemoteHistory, deleteWorkflow, getHistory, getWorkflows, saveWorkflow } from "./api";
import AuthScreen from "./auth/AuthScreen";
import { useAuth } from "./auth/AuthContext";
import CategoryRail from "./components/CategoryRail";
import HistoryPanel from "./components/HistoryPanel";
import PromptComposer from "./components/PromptComposer";
import ResultPanel from "./components/ResultPanel";

const CALCULATORS = [
  { id: "arithmetic", name: "Arithmetic", description: "Expressions and powers", examples: ["Calculate (18 + 6) * 4 / 3"] },
  { id: "age", name: "Age & dates", description: "Exact calendar differences", examples: ["My date of birth is 2003-08-15. Calculate my age."] },
  { id: "emi", name: "Loan EMI", description: "Payments and interest", examples: ["EMI for ₹10 lakh at 8.5% for 5 years"] },
  { id: "statistics", name: "Statistics", description: "Describe numeric datasets", examples: ["Find mean, median and standard deviation of 12, 15, 18, 21"] },
  { id: "units", name: "Unit conversion", description: "Units and dimensions", examples: ["Convert 15 kilometres to miles"] },
];

const DEFAULT_EXAMPLES = [
  "EMI for ₹10 lakh at 8.5% for 5 years",
  "Convert 15 kilometres to miles",
  "Mean of 12, 15, 18, 21",
];

export default function App() {
  const { user, loading: authLoading, logout } = useAuth();
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [workflowState, setWorkflowState] = useState("");

  const examples = useMemo(() => {
    const calculator = CALCULATORS.find((item) => item.id === selected);
    return calculator?.examples || DEFAULT_EXAMPLES;
  }, [selected]);

  useEffect(() => {
    let active = true;
    if (!user) {
      setHistory([]);
      setWorkflows([]);
      return () => { active = false; };
    }
    getHistory()
      .then(({ items }) => {
        if (!active) return;
        setHistory(items.map((item) => ({
          ...item.result,
          metadata: { ...item.result.metadata, history_id: item.id },
        })));
      })
      .catch(() => { if (active) setHistory([]); });
    getWorkflows()
      .then(({ items }) => { if (active) setWorkflows(items); })
      .catch(() => { if (active) setWorkflows([]); });
    return () => { active = false; };
  }, [user]);

  async function executeCalculation(nextQuery, calculator) {
    if (!nextQuery.trim()) return;
    setLoading(true);
    setError("");
    setWorkflowState("");
    try {
      const nextResult = await calculate(nextQuery, calculator);
      setResult(nextResult);
      setHistory((current) => [nextResult, ...current.filter((item) => item.query !== nextResult.query)].slice(0, 50));
    } catch (requestError) {
      setResult(null);
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    executeCalculation(query, selected);
  }

  function selectHistory(item) {
    setQuery(item.query);
    setSelected(item.calculator);
    setResult(item);
    setError("");
  }

  async function clearHistory() {
    try {
      await clearRemoteHistory();
      setHistory([]);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function saveCurrentWorkflow() {
    if (!result?.calcgraph) return;
    setWorkflowState("saving");
    try {
      const saved = await saveWorkflow(result.title, result.query, {
        query: result.query,
        calculator: result.calculator,
        calcgraph: result.calcgraph,
      });
      setWorkflows((current) => [saved, ...current]);
      setWorkflowState("saved");
    } catch (requestError) {
      setWorkflowState("");
      setError(requestError.message);
    }
  }

  function runWorkflow(workflow) {
    const definition = workflow.workflow_definition || {};
    const nextQuery = definition.query || workflow.description || "";
    const calculator = definition.calculator || null;
    setQuery(nextQuery);
    setSelected(calculator);
    executeCalculation(nextQuery, calculator);
  }

  async function removeWorkflow(workflowId) {
    try {
      await deleteWorkflow(workflowId);
      setWorkflows((current) => current.filter((item) => item.id !== workflowId));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  if (authLoading) return <div className="auth-loading"><div className="brand-mark">∑</div><span>Restoring secure session…</span></div>;
  if (!user) return <AuthScreen />;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-mark" aria-hidden="true"><span>∑</span></div>
        <div className="brand-copy">
          <strong>OmniCalc</strong>
          <span>CalcGraph</span>
        </div>
        <div className="topbar-status">
          <span className="status-dot" />
          Graph verifier online
        </div>
        <div className="account-chip">
          {user.avatar_url ? <img alt="" src={user.avatar_url} /> : <span>{(user.display_name || user.email)[0].toUpperCase()}</span>}
          <div><strong>{user.display_name || "OmniCalc user"}</strong><small>{user.email}</small></div>
          <button onClick={logout} type="button">Sign out</button>
        </div>
      </header>

      <div className="workspace-grid">
        <CategoryRail calculators={CALCULATORS} onSelect={setSelected} selected={selected} />
        <main className="main-workspace">
          <div className="workspace-heading">
            <div>
              <span className="eyebrow">Goal → graph → proof → result</span>
              <h1>Describe the outcome you need.</h1>
            </div>
            <p>Each request becomes a typed CalcGraph that is verified before deterministic execution.</p>
          </div>
          <PromptComposer
            examples={examples}
            loading={loading}
            onQueryChange={setQuery}
            onSubmit={handleSubmit}
            query={query}
          />
          <ResultPanel
            error={error}
            loading={loading}
            onSaveWorkflow={saveCurrentWorkflow}
            result={result}
            workflowState={workflowState}
          />
        </main>
        <HistoryPanel
          items={history}
          onClear={clearHistory}
          onDeleteWorkflow={removeWorkflow}
          onRunWorkflow={runWorkflow}
          onSelect={selectHistory}
          workflows={workflows}
        />
      </div>
    </div>
  );
}
