import { Navigate, Route, Routes, Link, useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "./context/AuthContext";
import LanguageSwitcher from "./components/LanguageSwitcher";
import Login from "./pages/Login";
import StudentDashboard from "./pages/StudentDashboard";
import ModuleView from "./pages/ModuleView";
import InstructorDashboard from "./pages/InstructorDashboard";
import LtiLanding from "./pages/LtiLanding";
import DemoPage from "./pages/DemoPage";
import SageApp from "./pages/SageApp";
import LmsSetupWizard from "./pages/LmsSetupWizard";
import SiteFooter from "./components/SiteFooter";
import { setTheme, currentTheme, type Theme } from "./lib/theme";
import { useState, type ReactNode } from "react";

function ThemeToggle() {
  const [theme, setThemeState] = useState<Theme>(currentTheme());
  const flip = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    setThemeState(next);
  };
  return (
    <button className="btn ghost" onClick={flip} title="Toggle light / dark theme"
      aria-label="Toggle dark mode" style={{ fontSize: 16, lineHeight: 1 }}>
      {theme === "dark" ? "☀" : "☾"}
    </button>
  );
}

function TopBar() {
  const { auth, logout } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const { t } = useTranslation();
  // The demo, Sage, and connect routes render their own chrome — hide the app top bar there.
  if (!auth || loc.pathname.startsWith("/demo") || loc.pathname.startsWith("/sage")
    || loc.pathname.startsWith("/connect")) return null;
  const home = auth.role === "student" ? "/dashboard" : "/instructor";
  return (
    <div className="topbar">
      <Link to={home} className="brand" style={{ color: "#fff" }}>
        LMS<span> Bridge</span>
      </Link>
      <div className="user">
        <span>{auth.full_name} · {auth.role}</span>
        <ThemeToggle />
        <LanguageSwitcher dark />
        <button className="btn ghost" onClick={() => { logout(); nav("/login"); }}>
          {t("common.signOut")}
        </button>
      </div>
    </div>
  );
}

function Protected({ children, roles }: { children: ReactNode; roles?: string[] }) {
  const { auth } = useAuth();
  if (!auth) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(auth.role)) {
    return <Navigate to={auth.role === "student" ? "/dashboard" : "/instructor"} replace />;
  }
  return <>{children}</>;
}

export default function App() {
  const { auth } = useAuth();
  const loc = useLocation();
  const isSage = loc.pathname.startsWith("/sage") || loc.pathname.startsWith("/connect");
  return (
    <div className="app-shell">
      <TopBar />
      <Routes>
        <Route path="/sage" element={<SageApp />} />
        <Route path="/connect" element={<LmsSetupWizard />} />
        <Route path="/lti" element={<LtiLanding />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/login" element={auth ? <Navigate to="/" replace /> : <Login />} />
        <Route
          path="/dashboard"
          element={<Protected roles={["student"]}><StudentDashboard /></Protected>}
        />
        <Route
          path="/modules/:id"
          element={<Protected><ModuleView /></Protected>}
        />
        <Route
          path="/instructor"
          element={
            <Protected roles={["instructor", "admin"]}><InstructorDashboard /></Protected>
          }
        />
        <Route
          path="*"
          element={
            <Navigate
              to={auth ? (auth.role === "student" ? "/dashboard" : "/instructor") : "/login"}
              replace
            />
          }
        />
      </Routes>
      {!isSage && <SiteFooter />}
    </div>
  );
}
