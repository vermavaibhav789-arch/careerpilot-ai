import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import TopbarAuth from "@/components/TopbarAuth";

export const metadata: Metadata = {
  title: "CareerPilot AI",
  description: "AI-powered resume match scoring and interview intelligence",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <AuthProvider>
          <header className="topbar">
            <Link href="/" className="wordmark">
              Career<span>Pilot</span> AI
            </Link>
            <div className="topbar-right">
              <nav className="nav">
                <Link href="/">Analyze</Link>
                <Link href="/interview">Interview</Link>
                <Link href="/resumes">Resumes</Link>
                <Link href="/applications">Applications</Link>
                <Link href="/career">Career</Link>
                <Link href="/career-dna">Career DNA</Link>
                <Link href="/dashboard">Dashboard</Link>
                <Link href="/pricing">Pricing</Link>
              </nav>
              <TopbarAuth />
            </div>
          </header>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
