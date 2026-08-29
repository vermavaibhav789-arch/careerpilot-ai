"use client";

import { useEffect, useRef, useState } from "react";
import { transcribeAudio } from "@/lib/api";

const MAX_SECONDS = 180; // auto-stop safety net so a forgotten recording doesn't run forever

type RecState = "idle" | "recording" | "transcribing" | "error";

interface AudioRecorderProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export default function AudioRecorder({ onTranscript, disabled }: AudioRecorderProps) {
  const [state, setState] = useState<RecState>("idle");
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // Stop the mic and any running timer if the component unmounts mid-recording
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = handleRecordingStopped;

      mediaRecorderRef.current = recorder;
      recorder.start();
      setState("recording");
      setSeconds(0);

      timerRef.current = setInterval(() => {
        setSeconds((s) => {
          if (s + 1 >= MAX_SECONDS) {
            stopRecording();
          }
          return s + 1;
        });
      }, 1000);
    } catch {
      setError(
        "Couldn't access your microphone. Check your browser's permission settings and try again."
      );
      setState("error");
    }
  }

  function stopRecording() {
    if (timerRef.current) clearInterval(timerRef.current);
    mediaRecorderRef.current?.stop();
    streamRef.current?.getTracks().forEach((t) => t.stop());
  }

  async function handleRecordingStopped() {
    setState("transcribing");
    const mimeType = mediaRecorderRef.current?.mimeType || "audio/webm";
    const blob = new Blob(chunksRef.current, { type: mimeType });

    try {
      const { transcript } = await transcribeAudio(blob, `answer.${extensionFor(mimeType)}`);
      onTranscript(transcript);
      setState("idle");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transcription failed.");
      setState("error");
    }
  }

  return (
    <div className="audio-recorder">
      {state === "idle" && (
        <button
          type="button"
          className="btn"
          onClick={startRecording}
          disabled={disabled}
        >
          ● Record answer
        </button>
      )}

      {state === "recording" && (
        <button type="button" className="btn recording" onClick={stopRecording}>
          ■ Stop recording — {formatTime(seconds)}
        </button>
      )}

      {state === "transcribing" && (
        <span className="loading-text">Transcribing your answer…</span>
      )}

      {state === "error" && (
        <div>
          <div className="error-banner">{error}</div>
          <button type="button" className="btn" onClick={() => setState("idle")}>
            Try again
          </button>
        </div>
      )}
    </div>
  );
}

function formatTime(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function extensionFor(mimeType: string): string {
  if (mimeType.includes("mp4")) return "mp4";
  if (mimeType.includes("ogg")) return "ogg";
  if (mimeType.includes("wav")) return "wav";
  return "webm";
}
