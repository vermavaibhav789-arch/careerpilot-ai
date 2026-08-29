"use client";

import { useEffect, useState } from "react";
import { downgradeToFree, getUsage, upgradeToPro } from "@/lib/api";
import type { Usage } from "@/lib/types";
import RequireAuth from "@/components/RequireAuth";

function limitLabel(value: number | null, unit: string): string {
  return value === null ? `Unlimited ${unit}` : `${value} ${unit}`;
}

function PricingContent() {
  const [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getUsage()
      .then(setUsage)
      .catch((err) => setError(err instanceof Error ? err.message : "Couldn't load your plan."))
      .finally(() => setLoading(false));
  }, []);

  async function handleUpgrade() {
    setSwitching(true);
    setError(null);
    try {
      setUsage(await upgradeToPro());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't upgrade.");
    } finally {
      setSwitching(false);
    }
  }

  async function handleDowngrade() {
    setSwitching(true);
    setError(null);
    try {
      setUsage(await downgradeToFree());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't downgrade.");
    } finally {
      setSwitching(false);
    }
  }

  const isPro = usage?.plan === "pro";

  return (
    <main className="page">
      <div className="intro">
        <h1>Plans</h1>
        <p>
          No payment is processed here yet — upgrading just switches your
          plan directly, for testing. See the note at the bottom for what
          that means before this goes anywhere near production.
        </p>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <p className="loading-text">Loading…</p>}

      {usage && (
        <div className="pricing-grid">
          <div className={`pricing-card ${!isPro ? "current" : ""}`}>
            <p className="pricing-tier-name">Free</p>
            <p className="pricing-price">$0</p>
            {!isPro && <span className="pricing-current-badge">Your current plan</span>}
            <ul className="pricing-feature-list">
              <li>{limitLabel(usage.limits.max_analyses, "resume analyses")}</li>
              <li>{limitLabel(usage.limits.max_interview_questions, "interview questions")}</li>
              <li>{limitLabel(usage.limits.max_voice_actions, "voice actions")}</li>
              <li>Cover letter generator</li>
              <li>ATS compatibility check</li>
              <li>Readiness score</li>
            </ul>
            {isPro && (
              <button className="btn" onClick={handleDowngrade} disabled={switching}>
                Switch to Free
              </button>
            )}
          </div>

          <div className={`pricing-card pricing-pro ${isPro ? "current" : ""}`}>
            <p className="pricing-tier-name">Pro</p>
            <p className="pricing-price">
              $9<span className="pricing-price-unit">/mo (illustrative)</span>
            </p>
            {isPro && <span className="pricing-current-badge">Your current plan</span>}
            <ul className="pricing-feature-list">
              <li>Unlimited resume analyses</li>
              <li>Resume optimizer (before/after bullet rewrites)</li>
              <li>Unlimited interview practice</li>
              <li>Unlimited voice interviews</li>
              <li>Advanced reports (weakness analysis + study recommendations)</li>
              <li>Career tracking (application tracker)</li>
              <li>Everything in Free</li>
            </ul>
            {!isPro && (
              <button className="btn btn-primary" onClick={handleUpgrade} disabled={switching}>
                {switching ? "Switching…" : "Upgrade to Pro →"}
              </button>
            )}
          </div>
        </div>
      )}

      {usage && (
        <div className="panel" style={{ marginTop: 24 }}>
          <p className="panel-label">Your usage</p>
          <div className="usage-row">
            <span>Resume analyses</span>
            <span>
              {usage.analyses_used}
              {usage.limits.max_analyses !== null ? ` / ${usage.limits.max_analyses}` : ""}
            </span>
          </div>
          <div className="usage-row">
            <span>Interview questions</span>
            <span>
              {usage.interview_questions_used}
              {usage.limits.max_interview_questions !== null
                ? ` / ${usage.limits.max_interview_questions}`
                : ""}
            </span>
          </div>
          <div className="usage-row">
            <span>Voice actions</span>
            <span>
              {usage.voice_actions_used}
              {usage.limits.max_voice_actions !== null ? ` / ${usage.limits.max_voice_actions}` : ""}
            </span>
          </div>
        </div>
      )}

      <p className="field-hint" style={{ marginTop: 24, maxWidth: "60ch" }}>
        Real payment integration (Stripe or Razorpay) isn't wired up — the
        "$9/mo" price is illustrative, and the upgrade button above sets your
        plan directly rather than charging anything. Wiring in a real
        processor means adding a checkout session + webhook handler in front
        of the same account.upgrade logic this button calls, not replacing it.
      </p>
    </main>
  );
}

export default function PricingPage() {
  return (
    <RequireAuth>
      <PricingContent />
    </RequireAuth>
  );
}
