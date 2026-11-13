import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import Overview from "./pages/Overview";
import UsersPage from "./pages/Users";
import TeamsPage from "./pages/Teams";
import RolesPage from "./pages/Roles";
import AuditLogsPage from "./pages/AuditLogs";
import SettingsPage from "./pages/Settings";

export default function App() {
  return <Routes><Route element={<AppLayout/>}><Route index element={<Overview/>}/><Route path="users" element={<UsersPage/>}/><Route path="teams" element={<TeamsPage/>}/><Route path="roles" element={<RolesPage/>}/><Route path="audit-logs" element={<AuditLogsPage/>}/><Route path="settings" element={<SettingsPage/>}/><Route path="*" element={<Navigate to="/" replace/>}/></Route></Routes>;
}
