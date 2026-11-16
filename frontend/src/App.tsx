import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import AppLayout from "./layouts/AppLayout";
import Overview from "./pages/Overview";
import UsersPage from "./pages/Users";
import TeamsPage from "./pages/Teams";
import RolesPage from "./pages/Roles";
import AuditLogsPage from "./pages/AuditLogs";
import SettingsPage from "./pages/Settings";
import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import OrganizationSetupPage from "./pages/OrganizationSetup";
import PlatformAdminPage from "./pages/PlatformAdmin";
import AcceptInvitationPage from "./pages/AcceptInvitation";
import { apiRequest } from "./lib/api";

function ProtectedLayout() {
  const { user, loading } = useAuth();
  if (loading) return <div className="grid min-h-screen place-items-center text-sm text-slate-500">Loading Nexus…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}

function WorkspaceRequired() {
  const { data, isLoading, error } = useQuery({queryKey:["organizations"],queryFn:()=>apiRequest<{id:string}[]>("/api/v1/organizations")});
  if (isLoading) return <div className="grid min-h-screen place-items-center text-sm text-slate-500">Checking workspace access…</div>;
  if (error || !data?.length) return <Navigate to="/setup" replace />;
  return <Outlet />;
}

function PublicOnly({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="grid min-h-screen place-items-center text-sm text-slate-500">Loading Nexus…</div>;
  return user ? <Navigate to="/" replace /> : <>{children}</>;
}

function AppRoutes() {
  return <Routes>
    <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />
    <Route path="/register" element={<PublicOnly><RegisterPage /></PublicOnly>} />
    <Route path="/accept-invitation" element={<AcceptInvitationPage />} />
    <Route element={<ProtectedLayout />}>
      <Route path="/setup" element={<OrganizationSetupPage />} />
      <Route path="/platform" element={<PlatformAdminPage />} />
      <Route element={<WorkspaceRequired />}>
        <Route element={<AppLayout />}>
          <Route index element={<Overview />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="teams" element={<TeamsPage />} />
          <Route path="roles" element={<RolesPage />} />
          <Route path="audit-logs" element={<AuditLogsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Route>
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>;
}

export default function App() {
  return <AuthProvider><AppRoutes /></AuthProvider>;
}
