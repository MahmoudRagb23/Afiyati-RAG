import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("afiyati_token")) {
      setReady(true);
      return;
    }
    api("/auth/me")
      .then(setUser)
      .catch(() => localStorage.removeItem("afiyati_token"))
      .finally(() => setReady(true));
  }, []);

  const value = useMemo(
    () => ({
      user,
      ready,
      login(result) {
        localStorage.setItem("afiyati_token", result.token);
        setUser(result.user);
      },
      logout() {
        localStorage.removeItem("afiyati_token");
        setUser(null);
      },
      updateUser(next) {
        setUser((current) => ({ ...current, ...next }));
      },
    }),
    [user, ready],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);

