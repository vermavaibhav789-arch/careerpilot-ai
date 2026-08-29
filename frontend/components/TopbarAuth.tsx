"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function TopbarAuth() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  if (loading) return null;

  if (!user) {
    return (
      <div className="topbar-auth">
        <Link href="/login">Log in</Link>
        <Link href="/register" className="btn btn-primary btn-small">
          Sign up
        </Link>
      </div>
    );
  }

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <div className="topbar-auth">
      <span className="topbar-email">{user.email}</span>
      <button className="btn btn-small" onClick={handleLogout}>
        Log out
      </button>
    </div>
  );
}
