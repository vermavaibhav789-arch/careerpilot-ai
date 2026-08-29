"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { verifyEmail } from "@/lib/api";

function VerifyEmailInner() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token in the URL.");
      return;
    }
    verifyEmail(token)
      .then((r) => {
        setStatus("success");
        setMessage(r.message);
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Verification failed.");
      });
  }, [token]);

  if (status === "loading") return <p className="loading-text">Verifying…</p>;
  if (status === "error") return <div className="error-banner">{message}</div>;
  return <p className="feedback-text">{message}</p>;
}

export default function VerifyEmailPage() {
  return (
    <main className="page auth-page">
      <div className="panel auth-panel">
        <p className="panel-label">Email verification</p>
        <Suspense fallback={<p className="loading-text">Loading…</p>}>
          <VerifyEmailInner />
        </Suspense>
        <p className="auth-switch">
          <Link href="/">Go to CareerPilot →</Link>
        </p>
      </div>
    </main>
  );
}
