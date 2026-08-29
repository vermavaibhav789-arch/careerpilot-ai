"use client";

import { useState } from "react";
import Link from "next/link";
import { forgotPassword } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await forgotPassword(email);
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page auth-page">
      <div className="panel auth-panel">
        <p className="panel-label">Reset your password</p>

        {error && <div className="error-banner">{error}</div>}

        {sent ? (
          <p className="feedback-text">
            If an account exists for that email, a reset link has been sent.
            Check your inbox (and check the backend console if you're running
            in dev mode without SMTP configured).
          </p>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: "100%" }}>
              {loading ? "Sending…" : "Send reset link →"}
            </button>
          </form>
        )}

        <p className="auth-switch">
          <Link href="/login">Back to login</Link>
        </p>
      </div>
    </main>
  );
}
