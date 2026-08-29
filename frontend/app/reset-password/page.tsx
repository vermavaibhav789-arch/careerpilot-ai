"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { resetPassword } from "@/lib/api";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await resetPassword(token, password);
      setDone(true);
      setTimeout(() => router.push("/login"), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't reset password.");
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <div className="error-banner">
        No reset token in the URL. Use the link from your reset email.
      </div>
    );
  }

  if (done) {
    return <p className="feedback-text">Password reset. Redirecting you to log in…</p>;
  }

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="error-banner">{error}</div>}
      <div className="field">
        <label htmlFor="password">New password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={8}
          required
        />
        <p className="field-hint">At least 8 characters.</p>
      </div>
      <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: "100%" }}>
        {loading ? "Resetting…" : "Reset password →"}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="page auth-page">
      <div className="panel auth-panel">
        <p className="panel-label">Set a new password</p>
        <Suspense fallback={<p className="loading-text">Loading…</p>}>
          <ResetPasswordForm />
        </Suspense>
        <p className="auth-switch">
          <Link href="/login">Back to login</Link>
        </p>
      </div>
    </main>
  );
}
