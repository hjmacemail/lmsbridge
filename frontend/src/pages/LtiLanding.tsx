import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api, saveToken } from "../api/client";
import type { AuthToken } from "../types";

/**
 * Landing page for LTI single sign-on. The backend redirects here after a validated
 * launch with a short-lived token in the URL; we adopt it as the session and route the
 * user to the right view (student or instructor).
 */
export default function LtiLanding() {
  const [params] = useSearchParams();
  const { adoptToken } = useAuth();
  const nav = useNavigate();
  const [err, setErr] = useState<string | null>(null);
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    const accessToken = params.get("token");
    const role = (params.get("role") || "student") as AuthToken["role"];
    const courseId = params.get("course_id");
    if (!accessToken) { setErr("Missing launch token."); return; }

    // Seed storage so the /auth/me request is authenticated, then build a full session.
    const partial: AuthToken = {
      access_token: accessToken, token_type: "bearer", role, user_id: 0, full_name: "",
    };
    saveToken(partial);
    api.me()
      .then((me) => {
        adoptToken({
          ...partial, user_id: me.id, full_name: me.full_name, role: me.role,
          is_platform_admin: me.is_platform_admin,
        });
        // Carry the launch's course context so the instructor view scopes to that course
        // (LMS-wide install → the instructor arrives inside one specific course).
        const dest = me.role === "student"
          ? "/dashboard"
          : `/instructor${courseId ? `?course_id=${courseId}` : ""}`;
        nav(dest, { replace: true });
      })
      .catch((e) => setErr((e as Error).message));
  }, [params, adoptToken, nav]);

  return (
    <div className="container">
      {err
        ? <div className="card error">Could not complete sign-in: {err}</div>
        : <p className="muted">Signing you in from your LMS…</p>}
    </div>
  );
}
