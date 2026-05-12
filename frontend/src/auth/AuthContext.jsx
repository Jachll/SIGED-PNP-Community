import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { fetchCurrentUser, loginRequest, subscribeToAuthEvents } from "../services/api";
import { buildAuthMessage, getAuthEventMessage, resolveRestoreSessionErrorState } from "./authState";
import {
  clearStoredAuthSession,
  isAuthSessionExpired,
  persistAuthSession,
  readStoredAuthSession
} from "./storage";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [authState, setAuthState] = useState({
    status: "restoring",
    session: null,
    message: null
  });

  useEffect(() => {
    let isMounted = true;

    async function restoreSession() {
      const storedSession = readStoredAuthSession();

      if (!storedSession) {
        if (isMounted) {
          setAuthState({
            status: "unauthenticated",
            session: null,
            message: null
          });
        }
        return;
      }

      if (isAuthSessionExpired(storedSession)) {
        clearStoredAuthSession();
        if (isMounted) {
          setAuthState({
            status: "unauthenticated",
            session: null,
            message: buildAuthMessage("Tu sesion expiro. Inicia sesion nuevamente.", "warning")
          });
        }
        return;
      }

      if (isMounted) {
        setAuthState({
          status: "restoring",
          session: storedSession,
          message: null
        });
      }

      try {
        const currentUser = await fetchCurrentUser();
        if (!isMounted) {
          return;
        }

        const nextSession = persistAuthSession({
          ...storedSession,
          user: currentUser
        });

        if (!nextSession) {
          clearStoredAuthSession();
          setAuthState({
            status: "unauthenticated",
            session: null,
            message: buildAuthMessage(
              "No se pudo restaurar la sesion guardada. Inicia sesion nuevamente.",
              "warning"
            )
          });
          return;
        }

        setAuthState({
          status: "authenticated",
          session: nextSession,
          message: null
        });
      } catch (requestError) {
        if (!isMounted) {
          return;
        }

        if (requestError?.status === 401 || requestError?.status === 403) {
          clearStoredAuthSession();
        }

        setAuthState(resolveRestoreSessionErrorState(requestError, storedSession));
      }
    }

    void restoreSession();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    const unsubscribe = subscribeToAuthEvents((event) => {
      if (event?.status === 401) {
        clearStoredAuthSession();
        setAuthState({
          status: "unauthenticated",
          session: null,
          message: getAuthEventMessage(event)
        });
        return;
      }

      if (event?.status === 403) {
        setAuthState((currentState) => ({
          ...currentState,
          message: getAuthEventMessage(event)
        }));
      }
    });

    return unsubscribe;
  }, []);

  async function login(credentials) {
    setAuthState((currentState) => ({
      ...currentState,
      status: "authenticating",
      message: null
    }));

    try {
      const response = await loginRequest(credentials);
      const nextSession = persistAuthSession(response);

      if (!nextSession) {
        throw new Error("La respuesta de autenticacion no contiene una sesion valida.");
      }

      setAuthState({
        status: "authenticated",
        session: nextSession,
        message: null
      });

      return nextSession;
    } catch (requestError) {
      clearStoredAuthSession();
      setAuthState({
        status: "unauthenticated",
        session: null,
        message: null
      });
      throw requestError;
    }
  }

  function logout(message = "") {
    clearStoredAuthSession();
    setAuthState({
      status: "unauthenticated",
      session: null,
      message: buildAuthMessage(message, "success")
    });
  }

  function clearAuthMessage() {
    setAuthState((currentState) => ({
      ...currentState,
      message: null
    }));
  }

  const value = useMemo(
    () => ({
      status: authState.status,
      session: authState.session,
      user: authState.session?.user ?? null,
      authMessage: authState.message?.text ?? "",
      authMessageTone: authState.message?.tone ?? "info",
      isAuthenticated: authState.status === "authenticated",
      isAuthenticating: authState.status === "authenticating",
      isRestoring: authState.status === "restoring",
      login,
      logout,
      clearAuthMessage
    }),
    [authState]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth debe usarse dentro de AuthProvider");
  }

  return context;
}
