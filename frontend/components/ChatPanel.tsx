"use client";

import { useState } from "react";
import { sendChatMessage } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

export default function ChatPanel({ sessionId }: { sessionId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const { answer } = await sendChatMessage(sessionId, question);
      setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <p className="panel-label">Ask CareerPilot</p>

      {messages.length === 0 && (
        <p style={{ color: "var(--text-dim)", fontSize: 13, marginBottom: 16 }}>
          Try: "Why am I not a good match for this job?" or "Which of my
          projects best covers the missing skills?"
        </p>
      )}

      {messages.length > 0 && (
        <div className="chat-log">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`chat-msg ${
                m.role === "user" ? "chat-msg-user" : "chat-msg-assistant"
              }`}
            >
              <span className="role-label">
                {m.role === "user" ? "You" : "CareerPilot"}
              </span>
              {m.content}
            </div>
          ))}
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}
      {loading && <p className="loading-text">Thinking…</p>}

      <form className="chat-input-row" onSubmit={handleSend}>
        <input
          type="text"
          placeholder="Ask a question about your match…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="btn" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
