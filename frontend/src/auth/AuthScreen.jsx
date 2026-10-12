import { useState } from "react";

import { useAuth } from "./AuthContext";
import GoogleSignIn from "./GoogleSignIn";

export default function AuthScreen({ onBack }) {
  const { login, register, google } = useAuth();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ display_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function run(action) {
    setBusy(true); setError("");
    try { await action(); } catch (requestError) { setError(requestError.message); } finally { setBusy(false); }
  }

  function submit(event) {
    event.preventDefault();
    run(() => mode === "login" ? login({ email: form.email, password: form.password }) : register(form));
  }

  return (
    <main className="auth-page auth-page-focused">
      <section className="auth-story auth-story-compact">
        <button className="back-to-overview" onClick={onBack} type="button">← Back to project overview</button>
        <div className="brand-lockup"><span>∑</span><strong>OmniCalc</strong><small>CalcGraph</small></div>
        <span className="eyebrow">Secure calculation workspace</span>
        <h1>Your calculations.<br />Your evidence.<br />One workspace.</h1>
        <p>Sign in to preserve calculation history, build reusable workflows and revisit verified CalcGraph receipts.</p>
        <div className="auth-promise-list"><span>✓ Short-lived JWT access</span><span>✓ Rotating secure refresh sessions</span><span>✓ Server-verified Google identity</span></div>
      </section>

      <section className="auth-card">
        <div className="auth-tabs">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")} type="button">Sign in</button>
          <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")} type="button">Create account</button>
        </div>
        <div className="auth-card-copy">
          <h2>{mode === "login" ? "Welcome back" : "Create your workspace"}</h2>
          <p>{mode === "login" ? "Continue to your personal home, history and saved workflows." : "Start a private workspace for reproducible calculations."}</p>
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
        <p className="auth-security">Protected account · Personal history · Verified workflows</p>
      </section>
    </main>
  );
}
