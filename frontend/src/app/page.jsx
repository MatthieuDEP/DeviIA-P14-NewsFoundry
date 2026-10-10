"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ChatWorkspace from "@/components/ChatWorkspace";
import { getToken, getUser, logout } from "@/lib/auth";
import styles from "./page.module.css";

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    async function checkSession() {
      try {
        const token = getToken();
        if (!token) {
          router.replace("/connexion");
          return;
        }
        const currentUser = await getUser(token);
        if (active) setUser(currentUser);
      } catch (cause) {
        if (!active) return;
        if (cause.status === 401) {
          try {
            logout();
          } catch {
            setError("Votre navigateur ne permet pas de réinitialiser la connexion.");
            return;
          }
          router.replace("/connexion");
        } else {
          setError(cause.message);
        }
      }
    }
    checkSession();
    return () => { active = false; };
  }, [router, attempt]);

  const handleLogout = useCallback(() => {
    try {
      logout();
      router.replace("/connexion");
    } catch {
      setError("Votre navigateur ne permet pas de réinitialiser la connexion.");
    }
  }, [router]);

  if (!user) {
    return (
      <main className={styles.loading}>
        {error ? (
          <section className={styles.errorCard} aria-labelledby="error-title">
            <h1 id="error-title">Connexion au service interrompue</h1>
            <p role="alert">{error}</p>
            <button type="button" onClick={() => { setError(""); setAttempt(attempt + 1); }}>
              Réessayer
            </button>
            <button type="button" onClick={handleLogout}>Se déconnecter</button>
          </section>
        ) : (
          <p role="status">Vérification de votre connexion…</p>
        )}
      </main>
    );
  }

  return <ChatWorkspace user={user} onLogout={handleLogout} sessionError={error} />;
}
