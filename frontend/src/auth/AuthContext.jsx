import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { getCurrentUser, loginAccount, loginWithGoogle, logoutAccount, registerAccount } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function restore() {
      try {
        const current = await getCurrentUser();
        if (active) setUser(current);
      } catch {
        if (active) setUser(null);
      } finally {
        if (active) setLoading(false);
      }
    }
    restore();
    return () => { active = false; };
  }, []);

  const value = useMemo(() => ({
    user,
    loading,
    async login(payload) { const data = await loginAccount(payload); setUser(data.user); },
    async register(payload) { const data = await registerAccount(payload); setUser(data.user); },
    async google(credential) { const data = await loginWithGoogle(credential); setUser(data.user); },
    async logout() { await logoutAccount(); setUser(null); },
  }), [loading, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
