"use client";

import { useEffect, useRef, useState } from "react";
import { fetchQuestionAudio } from "@/lib/api";

type State = "loading" | "playing" | "paused" | "blocked" | "error";

export default function QuestionAudio({
  sessionId,
  questionId,
}: {
  sessionId: string;
  questionId: string;
}) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const [state, setState] = useState<State>("loading");

  useEffect(() => {
    let cancelled = false;
    setState("loading");

    fetchQuestionAudio(sessionId, questionId)
      .then((objectUrl) => {
        if (cancelled) {
          URL.revokeObjectURL(objectUrl);
          return;
        }
        objectUrlRef.current = objectUrl;
        const audio = new Audio(objectUrl);
        audioRef.current = audio;

        audio.onended = () => setState("paused");
        audio.onerror = () => setState("error");

        // Autoplay only succeeds in some browsers even after a prior user
        // gesture (like clicking "Next question") - if it's blocked, fall
        // back to a visible play button rather than failing silently.
        audio
          .play()
          .then(() => setState("playing"))
          .catch(() => setState("blocked"));
      })
      .catch(() => {
        if (!cancelled) setState("error");
      });

    return () => {
      cancelled = true;
      audioRef.current?.pause();
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    };
  }, [sessionId, questionId]);

  function toggle() {
    const audio = audioRef.current;
    if (!audio) return;
    if (state === "playing") {
      audio.pause();
      setState("paused");
    } else {
      audio
        .play()
        .then(() => setState("playing"))
        .catch(() => setState("error"));
    }
  }

  // Question text is always visible regardless - audio is a bonus, so a
  // failure here shouldn't block the interview.
  if (state === "error") return null;

  return (
    <button type="button" className="btn audio-toggle" onClick={toggle} disabled={state === "loading"}>
      {state === "loading" && "⋯ loading audio"}
      {state === "playing" && "⏸ pause"}
      {(state === "paused" || state === "blocked") && "▶ play question"}
    </button>
  );
}
