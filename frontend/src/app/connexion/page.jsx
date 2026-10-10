"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import RobotIcon from "@/components/RobotIcon";
import { login } from "@/lib/auth";
import styles from "./page.module.css";

export default function LoginPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const errorRef = useRef(null);
  const submittingRef = useRef(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (submittingRef.current) return;
    submittingRef.current = true;
    setIsLoading(true);
    setError("");
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await login(data.get("email"), data.get("password"));
      form.reset();
      router.replace("/");
    } catch (cause) {
      setError(cause.message);
      requestAnimationFrame(() => errorRef.current?.focus());
    } finally {
      submittingRef.current = false;
      setIsLoading(false);
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.card} aria-labelledby="login-title">
        <h1 id="login-title" className={styles.brand}>NEWSFOUNDRY <RobotIcon /></h1>
        <p className={styles.description}>
          Connectez-vous pour accéder à votre assistant d’actualités IA
        </p>
        <form method="post" onSubmit={handleSubmit} className={styles.form} aria-busy={isLoading}>
          <div className={styles.field}>
            <label htmlFor="email">Adresse email</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="username"
              placeholder="votre.email@exemple.com"
              maxLength={254}
              required
              disabled={isLoading}
              aria-describedby={error ? "login-error" : undefined}
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              maxLength={72}
              required
              disabled={isLoading}
              aria-describedby={error ? "login-error" : undefined}
            />
          </div>
          <div aria-live="polite" aria-atomic="true">
            {error && (
              <p id="login-error" ref={errorRef} tabIndex={-1} className={styles.error}>
                {error}
              </p>
            )}
          </div>
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Connexion…" : "Se connecter"}
          </button>
        </form>
      </section>
    </main>
  );
}
