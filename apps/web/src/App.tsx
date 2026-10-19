import { useEffect, useState, type FormEvent } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";

import { authenticate, endSession, type User } from "./lib/auth";

type ApiState = "checking" | "online" | "offline";
type AuthMode = "login" | "signup";

export default function App() {
  return (
    <BrowserRouter>
      <AuthenticatedApplication />
    </BrowserRouter>
  );
}

function AuthenticatedApplication() {
  const navigate = useNavigate();
  const [apiState, setApiState] = useState<ApiState>("checking");
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState("");
  const [authChecked, setAuthChecked] = useState(false);
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let isMounted = true;

    fetch("/ready", { cache: "no-store" })
      .then((response) => {
        if (!response.ok) throw new Error("API is not ready");
        if (isMounted) setApiState("online");
      })
      .catch(() => {
        if (isMounted) setApiState("offline");
      });

    authenticate("refresh")
      .then((session) => {
        if (isMounted) {
          setUser(session.user);
          setAccessToken(session.access_token);
        }
      })
      .catch(() => undefined)
      .finally(() => {
        if (isMounted) setAuthChecked(true);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  async function submitCredentials(event: FormEvent<HTMLFormElement>, mode: AuthMode) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      const session = await authenticate(mode, {
        email,
        password,
        ...(mode === "signup" ? { display_name: displayName } : {}),
      });
      setUser(session.user);
      setAccessToken(session.access_token);
      setPassword("");
      navigate("/dashboard", { replace: true });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to sign in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function signOut() {
    try {
      await endSession();
    } finally {
      setUser(null);
      setAccessToken("");
      navigate("/login", { replace: true });
    }
  }

  const authView = (mode: AuthMode) => (
    <section className="auth-layout" aria-labelledby="auth-title">
      <div className="auth-intro">
        <p className="eyebrow">A workspace for learning</p>
        <h1>Make the hard concepts click.</h1>
        <p className="welcome-copy">
          ScalerMind brings your computer science learning into one focused place.
          Your mentor, curriculum, and practice tools are being built phase by phase.
        </p>
        <div className="phase-note">
          <span className="phase-index">02</span>
          <div>
            <strong>Secure sign-in</strong>
            <span>Create an account or sign in to reach your protected workspace.</span>
          </div>
        </div>
      </div>

      <div className="auth-card">
        <div className="auth-heading">
          <p className="eyebrow">{mode === "login" ? "Welcome back" : "Get started"}</p>
          <h2 id="auth-title">{mode === "login" ? "Sign in" : "Create account"}</h2>
          <p>{mode === "login" ? "Continue to your learning workspace." : "Your account is ready in a moment."}</p>
        </div>
        <form className="auth-form" onSubmit={(event) => submitCredentials(event, mode)}>
          {mode === "signup" && (
            <label>
              <span>Name</span>
              <input
                autoComplete="name"
                maxLength={120}
                onChange={(event) => setDisplayName(event.target.value)}
                required
                value={displayName}
              />
            </label>
          )}
          <label>
            <span>Email</span>
            <input
              autoComplete="email"
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </label>
          <label>
            <span>Password</span>
            <input
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              minLength={mode === "signup" ? 12 : 1}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
            {mode === "signup" && <small>Use at least 12 characters.</small>}
          </label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="primary-button" disabled={isSubmitting || apiState === "offline"} type="submit">
            {isSubmitting ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
        <p className="auth-switch">
          {mode === "login" ? "New to ScalerMind?" : "Already have an account?"}{" "}
          <Link to={mode === "login" ? "/signup" : "/login"}>
            {mode === "login" ? "Create an account" : "Sign in"}
          </Link>
        </p>
      </div>
    </section>
  );

  const loadingView = (
    <section className="welcome-panel signed-in-panel" aria-live="polite">
      <p className="eyebrow">Secure session</p>
      <h1>Restoring your workspace.</h1>
      <p className="welcome-copy">Checking your sign-in before opening this protected page.</p>
    </section>
  );

  const dashboardView = user && (
    <section className="welcome-panel signed-in-panel" aria-labelledby="welcome-title">
      <p className="eyebrow">Your learning workspace</p>
      <h1 id="welcome-title">Welcome, {user.display_name}.</h1>
      <p className="welcome-copy">
        You are signed in as {user.email}. Your protected ScalerMind workspace is ready.
      </p>
      <div className="phase-note">
        <span className="phase-index">{user.role === "admin" ? "AD" : "01"}</span>
        <div>
          <strong>{user.role === "admin" ? "Administrator" : "Learner account"}</strong>
          <span>Authentication is active. The curriculum and mentor tools arrive in later phases.</span>
        </div>
      </div>
      <div className="signed-in-actions">
        <span className="token-note">Session protected</span>
        <button className="secondary-button" onClick={signOut} type="button">Sign out</button>
      </div>
      <span className="sr-only" aria-live="polite">{accessToken ? "Signed in" : ""}</span>
    </section>
  );

  return (
    <main className="page-shell">
      <header className="topbar">
        <Link className="wordmark" to="/" aria-label="ScalerMind home">
          <span className="wordmark-mark" aria-hidden="true">S</span>
          <span>scalermind</span>
        </Link>
        <div className={`service-status service-status--${apiState}`} role="status">
          <span className="status-dot" aria-hidden="true" />
          {{ checking: "Checking API", online: "API ready", offline: "API unavailable" }[apiState]}
        </div>
      </header>

      <Routes>
        <Route path="/" element={!authChecked ? loadingView : <Navigate to={user ? "/dashboard" : "/login"} replace />} />
        <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : authView("login")} />
        <Route path="/signup" element={user ? <Navigate to="/dashboard" replace /> : authView("signup")} />
        <Route
          path="/dashboard"
          element={!authChecked ? loadingView : user ? dashboardView : <Navigate to="/login" replace />}
        />
        <Route path="*" element={!authChecked ? loadingView : <Navigate to={user ? "/dashboard" : "/login"} replace />} />
      </Routes>

      <footer className="page-footer">
        <span>ScalerMind</span>
        <span>Built for deliberate practice</span>
      </footer>
    </main>
  );
}
