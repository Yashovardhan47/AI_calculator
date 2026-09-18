import { useState } from "react";

import { useAuth } from "./AuthContext";
import GoogleSignIn from "./GoogleSignIn";

export default function AuthScreen() {
  const { login, register, google } = useAuth();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ display_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function run(action) {
    setBusy(true);
    setError("");
    try { await action(); } catch (requestError) { setError(requestError.message); } finally { setBusy(false); }
  }

  function submit(event) {
    event.preventDefault();
    run(() => mode === "login" ? login({ email: form.email, password: form.password }) : register(form));
  }

  return (
    <main className="auth-page">
      <section className="auth-story">
        <div className="brand-lockup"><span>∑</span><strong>OmniCalc</strong><small>CalcGraph</small></div>
        <span className="eyebrow">AI calculation operating system</span>
        <h1>Ask naturally.<br />Calculate verifiably.</h1>
        <p>OmniCalc translates your goal into a typed calculation graph, verifies every dependency, and executes trusted mathematical tools.</p>
        <div className="auth-feature-grid">
          <article><strong>Typed graphs</strong><span>Every input and formula has a machine-checkable type.</span></article>
          <article><strong>Deterministic tools</strong><span>AI plans the work; verified engines calculate the answer.</span></article>
          <article><strong>Evidence receipts</strong><span>Replay results with formula lineage and reproducibility hashes.</span></article>
        </div>
      </section>

      <section className="auth-card">
        <div className="auth-tabs">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")} type="button">Sign in</button>
          <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")} type="button">Create account</button>
        </div>
        <div className="auth-card-copy">
          <h2>{mode === "login" ? "Welcome back" : "Create your workspace"}</h2>
          <p>{mode === "login" ? "Continue to your calculation history and saved workflows." : "Save, compare, and reproduce verified calculations."}</p>
        </div>
        <GoogleSignIn disabled={busy} onCredential={(credential) => run(() => google(credential))} />
        <div className="auth-divider"><span>or continue with email</span></div>
        <form className="auth-form" onSubmit={submit}>
          {mode === "register" && <label>Display name<input autoComplete="name" minLength={2} onChange={(event) => setForm({ ...form, display_name: event.target.value })} required value={form.display_name} /></label>}
          <label>Email<input autoComplete="email" onChange={(event) => setForm({ ...form, email: event.target.value })} required type="email" value={form.email} /></label>
          <label>Password<input autoComplete={mode === "login" ? "current-password" : "new-password"} minLength={mode === "login" ? 1 : 10} onChange={(event) => setForm({ ...form, password: event.target.value })} required type="password" value={form.password} /></label>
          {mode === "register" && <small>At least 10 characters with uppercase, lowercase, and a number.</small>}
          {error && <div className="auth-error" role="alert">{error}</div>}
          <button className="auth-submit" disabled={busy} type="submit">{busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}</button>
        </form>
        <p className="auth-security">Short-lived JWT access · Rotating refresh session · Server-verified Google identity</p>
      </section>
    </main>
  );
}
