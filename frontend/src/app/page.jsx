"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import RobotIcon from "@/components/RobotIcon";
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

  function handleLogout() {
    try {
      logout();
      router.replace("/connexion");
    } catch {
      setError("Votre navigateur ne permet pas de réinitialiser la connexion.");
    }
  }

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

  return (
    <div className={styles.page}>
      <a className={styles.skipLink} href="#main-content">Aller au contenu</a>
      <aside className={styles.sidebar} aria-label="Votre compte">
        <div className={styles.brand}>NEWSFOUNDRY <RobotIcon size={18} /></div>
        <div className={styles.account}>
          <p>VOTRE COMPTE</p>
          <span>{user.email}</span>
        </div>
        <button type="button" className={styles.logout} onClick={handleLogout}>
          Se déconnecter
        </button>
        {error && <p role="alert" className={styles.logoutError}>{error}</p>}
      </aside>
      <div className={styles.workspace}>
        <header className={styles.header}><span>Votre espace</span></header>
        <main id="main-content" className={styles.main} tabIndex={-1}>
          <section className={styles.card} aria-labelledby="welcome-title">
            <div className={styles.robot}><RobotIcon size={80} /></div>
            <h1 id="welcome-title">Assistant Revue de Presse IA</h1>
            <p>Bienvenue dans votre espace NewsFoundry.</p>
            <div className={styles.identity}>
              <strong>Connexion réussie</strong>
              <span>{user.email}</span>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
