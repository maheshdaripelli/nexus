import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
type Organization = { id: string; name: string; slug: string; created_at: string };
type PlatformOverview = { organization_count: number; user_count: number; membership_count: number };

export default function OrganizationSetupPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [error, setError] = useState("");
  const [signingOut, setSigningOut] = useState(false);
  const navigate = useNavigate();
  const { logout } = useAuth();
  const platformAccess = useQuery({
    queryKey: ["platform-access"],
    queryFn: () => apiRequest<PlatformOverview>("/api/v1/platform/overview"),
    retry: false,
  });

  useEffect(() => {
    let active = true;
    apiRequest<Organization[]>("/api/v1/organizations")
      .then(items => {
        if (!active) return;
        setOrganizations(items);
        if (items.length === 1) {
          localStorage.setItem("nexus.organization_id", items[0].id);
          navigate("/", { replace: true });
        }
      })
      .catch(e => { if (active) setError(e instanceof Error ? e.message : "Could not load workspaces"); });
    return () => { active = false; };
  }, [navigate]);

  function select(org: Organization) {
    localStorage.setItem("nexus.organization_id", org.id);
    navigate("/", { replace: true });
  }

  async function signOut() {
    setSigningOut(true);
    try { await logout(); }
    catch { /* The auth context clears the local session even if the API is unavailable. */ }
    finally {
      localStorage.removeItem("nexus.organization_id");
      navigate("/login", { replace: true });
      setSigningOut(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f7f8fc] px-4 py-10 sm:px-6">
      <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <p className="text-lg font-bold text-indigo-700">◆ nexus</p>
        <h1 className="mt-8 text-2xl font-bold">{organizations.length ? "Choose your workspace" : "Workspace access required"}</h1>
        <p className="mt-2 text-sm leading-6 text-slate-500">
          {organizations.length
            ? "Choose which organization you want to work in. Permissions are specific to each workspace."
            : "Your account is active, but you haven’t been added to an organization yet. If you are an organization user, ask an Owner or Admin to invite you. If you are the Platform Super Admin, open platform administration below to create your first organization."}
        </p>
        {error && <p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {organizations.map(org => (
          <button key={org.id} onClick={() => select(org)} className="mt-3 flex w-full items-center justify-between gap-3 rounded-lg border border-slate-200 p-4 text-left hover:border-indigo-300">
            <span className="min-w-0"><span className="block truncate text-sm font-semibold">{org.name}</span><span className="text-xs text-slate-400">{org.slug}</span></span>
            <span className="text-xs font-semibold text-indigo-600">Open →</span>
          </button>
        ))}
        {platformAccess.isSuccess && (
          <div className="mt-5 rounded-lg border border-indigo-100 bg-indigo-50 p-4">
            <strong className="text-sm text-indigo-900">Platform Super Admin access detected</strong>
            <p className="mt-1 text-xs leading-5 text-indigo-800">You do not need an organization membership to administer Nexus. Create your first workspace and invite its initial Owner.</p>
            <button onClick={() => navigate("/platform")} className="mt-3 rounded-lg bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-indigo-700">Open platform administration</button>
          </div>
        )}
        {platformAccess.isError && (
          <div className="mt-5 rounded-lg bg-amber-50 p-4 text-sm text-amber-800">
            <strong>Invitation-only access</strong>
            <p className="mt-1 text-xs leading-5">Ask your organization administrator to invite your work email. Public account creation and organization creation are disabled for regular users.</p>
          </div>
        )}
        <button disabled={signingOut} onClick={() => void signOut()} className="mt-6 text-sm font-semibold text-indigo-600 disabled:opacity-50">{signingOut ? "Signing out…" : "Sign out"}</button>
      </div>
    </main>
  );
}