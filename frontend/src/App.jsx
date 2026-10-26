import { useEffect, useMemo, useState } from "react";

import { calculate, clearRemoteHistory, deleteWorkflow, getHistory, getWorkflows, saveWorkflow } from "./api";
import AuthScreen from "./auth/AuthScreen";
import { useAuth } from "./auth/AuthContext";
import CategoryRail from "./components/CategoryRail";
import HistoryPanel from "./components/HistoryPanel";
import PromptComposer from "./components/PromptComposer";
import ResultPanel from "./components/ResultPanel";

const CALCULATORS = [
  { id: "arithmetic", name: "Arithmetic", description: "Expressions and powers", icon: "±", examples: ["Calculate (18 + 6) * 4 / 3"] },
  { id: "age", name: "Age & dates", description: "Exact calendar differences", icon: "⌁", examples: ["My date of birth is 2003-08-15. Calculate my age."] },
  { id: "emi", name: "Loan EMI", description: "Payments and interest", icon: "₹", examples: ["EMI for ₹10 lakh at 8.5% for 5 years"] },
  { id: "statistics", name: "Statistics", description: "Describe numeric datasets", icon: "σ", examples: ["Find mean, median and standard deviation of 12, 15, 18, 21"] },
  { id: "units", name: "Unit conversion", description: "Units and dimensions", icon: "↔", examples: ["Convert 15 kilometres to miles"] },
  { id: "advanced", name: "Advanced", description: "Algebra, geometry, science & more", icon: "∫", examples: ["Solve 3x + 7 = 25", "Area of a circle with radius 12", "Calculate compound interest on 100000 at 8% for 5 years"] },
];

const DEFAULT_EXAMPLES = [
  "EMI for ₹10 lakh at 8.5% for 5 years",
  "Convert 15 kilometres to miles",
  "Standard deviation of 12, 18, 21, 23 and 31",
  "Solve 3x + 7 = 25",
  "Area of a circle with radius 12",
];

function Brand() {
  return <div className="site-brand"><span className="brand-mark">∑</span><div className="brand-copy"><strong>OmniCalc</strong><span>CalcGraph</span></div></div>;
}

function PublicLanding({ onAuthenticate }) {
  return (
    <div className="landing-page">
      <nav className="landing-nav">
        <Brand />
        <div className="landing-links"><a href="#capabilities">Capabilities</a><a href="#calcgraph">CalcGraph</a><a href="#domains">Domains</a></div>
        <button className="nav-cta" onClick={onAuthenticate} type="button">Sign in <span>→</span></button>
      </nav>
      <main>
        <section className="landing-hero">
          <div className="hero-copy">
            <span className="eyebrow">Verified intelligence for real-world calculation</span>
            <h1>One question.<br /><em>Every calculation.</em><br />Evidence included.</h1>
            <p>OmniCalc combines natural-language AI with CalcGraph, a typed verification layer that turns each request into a traceable, reproducible calculation—not a black-box guess.</p>
            <div className="hero-actions">
              <button className="primary-cta" onClick={onAuthenticate} type="button">Create your workspace <span>→</span></button>
              <a className="secondary-cta" href="#calcgraph">Explore how it works</a>
            </div>
            <div className="trust-row"><span><b>6+</b> calculation domains</span><span><b>Typed</b> formula graphs</span><span><b>100%</b> reproducible receipts</span></div>
          </div>
          <div className="hero-proof-card" aria-label="Example verified calculation">
            <div className="proof-top"><span>LIVE CALCULATION TRACE</span><i>Verifier online</i></div>
            <p className="proof-question">“Standard deviation of 12, 18, 21, 23 and 31”</p>
            <div className="proof-flow"><span>Natural language</span><b>→</b><span>Statistics graph</span><b>→</b><span>Verified result</span></div>
            <div className="proof-result"><small>Population standard deviation</small><strong>6.2290</strong></div>
            <ul><li><span>✓</span> Inputs parsed and typed</li><li><span>✓</span> Formula registered</li><li><span>✓</span> Deterministic execution</li></ul>
            <div className="proof-hash">receipt · cg_87a4…e921</div>
          </div>
        </section>

        <section className="capability-section" id="capabilities">
          <div className="section-heading"><span className="eyebrow">The complete perspective</span><h2>AI plans. Trusted engines calculate.</h2><p>Designed for people who need understandable answers across personal, academic, scientific and financial work.</p></div>
          <div className="capability-grid">
            <article><span>01</span><h3>Ask naturally</h3><p>Describe the result you need without memorizing formulas or rigid syntax.</p></article>
            <article><span>02</span><h3>Build a CalcGraph</h3><p>Your intent becomes a typed graph of inputs, operations and dependencies.</p></article>
            <article><span>03</span><h3>Verify before execution</h3><p>Units, formula constraints and graph safety are checked before calculation.</p></article>
            <article><span>04</span><h3>Keep the evidence</h3><p>Save history, workflows, assumptions and replayable verification receipts.</p></article>
          </div>
        </section>

        <section className="graph-story" id="calcgraph">
          <div><span className="eyebrow">Research contribution</span><h2>CalcGraph makes AI calculation inspectable.</h2><p>Instead of asking an AI model to invent an answer, OmniCalc uses AI only to understand intent. CalcGraph compiles that intent into a constrained representation, verifies it, and sends it to deterministic tools.</p><button className="text-cta" onClick={onAuthenticate} type="button">Start a verified calculation →</button></div>
          <div className="graph-visual">
            <div><small>INPUT</small><strong>User intent</strong><code>radius = 12</code></div><b>→</b>
            <div><small>GRAPH</small><strong>circle.area</strong><code>π × r²</code></div><b>→</b>
            <div><small>PROOF</small><strong>Verified</strong><code>452.389</code></div>
          </div>
        </section>

        <section className="domain-section" id="domains">
          <div className="section-heading"><span className="eyebrow">Calculation universe</span><h2>Built to grow across domains.</h2></div>
          <div className="domain-grid">{CALCULATORS.map((item) => <article key={item.id}><span>{item.icon}</span><div><h3>{item.name}</h3><p>{item.description}</p></div></article>)}</div>
        </section>

        <section className="landing-final"><span className="eyebrow">Your verified workspace awaits</span><h2>Move from a question to an answer you can trust.</h2><button className="primary-cta" onClick={onAuthenticate} type="button">Sign in or create an account <span>→</span></button></section>
      </main>
      <footer className="landing-footer"><Brand /><p>Natural-language calculation with deterministic proof.</p><span>OmniCalc · CalcGraph research platform</span></footer>
    </div>
  );
}

function UserHome({ user, history, workflows, onOpenWorkspace, onRunExample, onLogout }) {
  const recent = history.slice(0, 3);
  return (
    <div className="home-page">
      <header className="home-nav">
        <Brand />
        <nav><button className="active" type="button">Home</button><button onClick={onOpenWorkspace} type="button">Calculator</button></nav>
        <div className="account-chip">
          {user.avatar_url ? <img alt="" src={user.avatar_url} /> : <span>{(user.display_name || user.email)[0].toUpperCase()}</span>}
          <div><strong>{user.display_name || "OmniCalc user"}</strong><small>{user.email}</small></div>
          <button onClick={onLogout} type="button">Sign out</button>
        </div>
      </header>
      <main className="home-content">
        <section className="home-welcome">
          <div><span className="eyebrow">Personal calculation command center</span><h1>Welcome back, {(user.display_name || "Explorer").split(" ")[0]}.</h1><p>What would you like to understand, compare or calculate today?</p></div>
          <button className="primary-cta" onClick={onOpenWorkspace} type="button">Open calculator <span>→</span></button>
        </section>

        <section className="home-stat-grid">
          <article><span>Calculation history</span><strong>{history.length}</strong><small>verified results saved</small></article>
          <article><span>Reusable workflows</span><strong>{workflows.length}</strong><small>ready to run again</small></article>
          <article><span>Available domains</span><strong>{CALCULATORS.length}</strong><small>one unified workspace</small></article>
          <article className="verified-stat"><span>Verification engine</span><strong>Online</strong><small>CalcGraph checks enabled</small></article>
        </section>

        <div className="home-grid">
          <section className="home-panel quick-start">
            <div className="panel-heading"><div><span className="eyebrow">Quick start</span><h2>Choose a calculation domain</h2></div><button onClick={onOpenWorkspace} type="button">View all →</button></div>
            <div className="home-domain-grid">{CALCULATORS.map((item) => <button key={item.id} onClick={() => onRunExample(item.examples[0], item.id)} type="button"><span>{item.icon}</span><div><strong>{item.name}</strong><small>{item.description}</small></div><b>→</b></button>)}</div>
          </section>

          <section className="home-panel recent-panel">
            <div className="panel-heading"><div><span className="eyebrow">Recent activity</span><h2>Your calculations</h2></div></div>
            {recent.length ? <div className="home-recent-list">{recent.map((item, index) => <button key={(item.metadata?.history_id || item.query) + index} onClick={() => onRunExample(item.query, item.calculator)} type="button"><span>{item.calculator}</span><strong>{item.query}</strong><small>{typeof item.answer === "string" ? item.answer : String(item.value ?? "Open result")}</small></button>)}</div> : <div className="home-empty"><span>∑</span><h3>No calculations yet</h3><p>Your verified results will appear here.</p><button onClick={onOpenWorkspace} type="button">Run your first calculation</button></div>}
          </section>
        </div>

        <section className="home-research-card">
          <div><span className="eyebrow">Why CalcGraph matters</span><h2>Every answer carries its reasoning structure.</h2><p>Inspect formula lineage, type checks, assumptions and a reproducibility fingerprint for serious work.</p></div>
          <div className="mini-pipeline"><span>Intent</span><b>→</b><span>Typed graph</span><b>→</b><span>Verification</span><b>→</b><span>Result</span></div>
        </section>
      </main>
    </div>
  );
}

export default function App() {
  const { user, loading: authLoading, logout } = useAuth();
  const [screen, setScreen] = useState("landing");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [workflowState, setWorkflowState] = useState("");

  const examples = useMemo(() => CALCULATORS.find((item) => item.id === selected)?.examples || DEFAULT_EXAMPLES, [selected]);

  useEffect(() => {
    if (user && (screen === "landing" || screen === "auth")) setScreen("home");
  }, [user, screen]);

  useEffect(() => {
    let active = true;
    if (!user) {
      setHistory([]);
      setWorkflows([]);
      return () => { active = false; };
    }
    getHistory().then(({ items }) => {
      if (active) setHistory(items.map((item) => ({ ...item.result, metadata: { ...item.result.metadata, history_id: item.id } })));
    }).catch(() => { if (active) setHistory([]); });
    getWorkflows().then(({ items }) => { if (active) setWorkflows(items); }).catch(() => { if (active) setWorkflows([]); });
    return () => { active = false; };
  }, [user]);

  async function executeCalculation(nextQuery, calculator) {
    if (!nextQuery.trim()) return;
    setLoading(true); setError(""); setWorkflowState("");
    try {
      const nextResult = await calculate(nextQuery, calculator);
      setResult(nextResult);
      setHistory((current) => [nextResult, ...current.filter((item) => item.query !== nextResult.query)].slice(0, 50));
    } catch (requestError) {
      setResult(null); setError(requestError.message);
    } finally { setLoading(false); }
  }

  function enterWorkspace(nextQuery = "", calculator = null) {
    setQuery(nextQuery); setSelected(calculator); setScreen("workspace");
    if (nextQuery) executeCalculation(nextQuery, calculator);
  }

  function selectHistory(item) { setQuery(item.query); setSelected(item.calculator); setResult(item); setError(""); }
  async function clearHistory() { try { await clearRemoteHistory(); setHistory([]); } catch (requestError) { setError(requestError.message); } }
  async function saveCurrentWorkflow() {
    if (!result?.calcgraph) return;
    setWorkflowState("saving");
    try {
      const saved = await saveWorkflow(result.title, result.query, { query: result.query, calculator: result.calculator, calcgraph: result.calcgraph });
      setWorkflows((current) => [saved, ...current]); setWorkflowState("saved");
    } catch (requestError) { setWorkflowState(""); setError(requestError.message); }
  }
  function runWorkflow(workflow) {
    const definition = workflow.workflow_definition || {};
    const nextQuery = definition.query || workflow.description || "";
    const calculator = definition.calculator || null;
    setQuery(nextQuery); setSelected(calculator); executeCalculation(nextQuery, calculator);
  }
  async function removeWorkflow(workflowId) { try { await deleteWorkflow(workflowId); setWorkflows((current) => current.filter((item) => item.id !== workflowId)); } catch (requestError) { setError(requestError.message); } }
  async function signOut() { await logout(); setScreen("landing"); }

  if (authLoading) return <div className="auth-loading"><div className="brand-mark">∑</div><span>Restoring secure session…</span></div>;
  if (!user && screen === "landing") return <PublicLanding onAuthenticate={() => setScreen("auth")} />;
  if (!user) return <AuthScreen onBack={() => setScreen("landing")} />;
  if (screen !== "workspace") return <UserHome history={history} onLogout={signOut} onOpenWorkspace={() => enterWorkspace()} onRunExample={enterWorkspace} user={user} workflows={workflows} />;

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand-home-button" onClick={() => setScreen("home")} type="button"><Brand /></button>
        <button className="workspace-back" onClick={() => setScreen("home")} type="button">← Home</button>
        <div className="topbar-status"><span className="status-dot" />Graph verifier online</div>
        <div className="account-chip">
          {user.avatar_url ? <img alt="" src={user.avatar_url} /> : <span>{(user.display_name || user.email)[0].toUpperCase()}</span>}
          <div><strong>{user.display_name || "OmniCalc user"}</strong><small>{user.email}</small></div>
          <button onClick={signOut} type="button">Sign out</button>
        </div>
      </header>
      <div className="workspace-grid">
        <CategoryRail calculators={CALCULATORS} onSelect={setSelected} selected={selected} />
        <main className="main-workspace">
          <div className="workspace-heading"><div><span className="eyebrow">Goal → graph → proof → result</span><h1>Describe the outcome you need.</h1></div><p>Each request becomes a typed CalcGraph that is verified before deterministic execution.</p></div>
          <PromptComposer examples={examples} loading={loading} onQueryChange={setQuery} onSubmit={(event) => { event.preventDefault(); executeCalculation(query, selected); }} query={query} />
          <ResultPanel error={error} loading={loading} onSaveWorkflow={saveCurrentWorkflow} result={result} workflowState={workflowState} />
        </main>
        <HistoryPanel items={history} onClear={clearHistory} onDeleteWorkflow={removeWorkflow} onRunWorkflow={runWorkflow} onSelect={selectHistory} workflows={workflows} />
      </div>
    </div>
  );
}

