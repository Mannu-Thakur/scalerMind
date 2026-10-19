import { useEffect, useState } from "react";

type ApiState = "checking" | "online" | "offline";

export default function App() {
  const [apiState, setApiState] = useState<ApiState>("checking");

  useEffect(() => {
    let isMounted = true;

    fetch("/ready", { cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error("API is not ready");
        }
        return response.json();
      })
      .then(() => {
        if (isMounted) setApiState("online");
      })
      .catch(() => {
        if (isMounted) setApiState("offline");
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const apiLabel = {
    checking: "Checking API",
    online: "API ready",
    offline: "API unavailable",
  }[apiState];

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="wordmark" href="/" aria-label="ScalerMind home">
          <span className="wordmark-mark" aria-hidden="true">S</span>
          <span>scalermind</span>
        </a>
        <div className={`service-status service-status--${apiState}`} role="status">
          <span className="status-dot" aria-hidden="true" />
          {apiLabel}
        </div>
      </header>

      <section className="welcome-panel" aria-labelledby="welcome-title">
        <p className="eyebrow">A workspace for learning</p>
        <h1 id="welcome-title">Make the hard concepts click.</h1>
        <p className="welcome-copy">
          ScalerMind brings your computer science learning into one focused place.
          Your mentor, curriculum, and practice tools are being built phase by phase.
        </p>
        <div className="phase-note">
          <span className="phase-index">01</span>
          <div>
            <strong>Local foundation</strong>
            <span>The application services are connected and ready for the next phase.</span>
          </div>
        </div>
      </section>

      <footer className="page-footer">
        <span>ScalerMind</span>
        <span>Built for deliberate practice</span>
      </footer>
    </main>
  );
}
