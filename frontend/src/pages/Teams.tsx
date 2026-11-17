import { type FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Users, Pencil, Trash2 } from "lucide-react";
import { Navigate } from "react-router-dom";
import SectionHeading from "../components/SectionHeading";
import { apiRequest } from "../lib/api";

type Team = { id: string; organization_id: string; name: string; description: string | null; created_at: string };
type Member = { user_id: string; full_name: string; email: string; role: string };
const orgId = () => localStorage.getItem("nexus.organization_id");

export default function TeamsPage() {
  const id = orgId();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [modalError, setModalError] = useState("");
  const [selected, setSelected] = useState<Team | null>(null);
  const [editing, setEditing] = useState<Team | null>(null);

  const teams = useQuery({
    queryKey: ["teams", id], enabled: !!id,
    queryFn: () => apiRequest<Team[]>(`/api/v1/organizations/${id}/teams`)
  });
  const members = useQuery({
    queryKey: ["members", id], enabled: !!id,
    queryFn: () => apiRequest<Member[]>(`/api/v1/organizations/${id}/members`)
  });
  const teamMembers = useQuery({
    queryKey: ["team-members", id, selected?.id], enabled: !!id && !!selected,
    queryFn: () => apiRequest<Member[]>(`/api/v1/organizations/${id}/teams/${selected?.id}/members`)
  });
  const refreshTeams = () => qc.invalidateQueries({ queryKey: ["teams", id] });
  const create = useMutation({
    mutationFn: () => apiRequest<Team>(`/api/v1/organizations/${id}/teams`, {
      method: "POST", body: JSON.stringify({ name, description: description || null })
    }),
    onSuccess: () => { setOpen(false); setModalError(""); setName(""); setDescription(""); refreshTeams(); },
    onError: e => setModalError(e instanceof Error ? e.message : "Could not create team")
  });
  const update = useMutation({
    mutationFn: () => apiRequest<Team>(`/api/v1/organizations/${id}/teams/${editing?.id}`, {
      method: "PATCH", body: JSON.stringify({ name, description: description || null })
    }),
    onSuccess: team => {
      setEditing(null); setModalError(""); setName(""); setDescription("");
      if (selected?.id === team.id) setSelected(team);
      refreshTeams();
    },
    onError: e => setModalError(e instanceof Error ? e.message : "Could not update team")
  });
  const remove = useMutation({
    mutationFn: (team: Team) => apiRequest<void>(`/api/v1/organizations/${id}/teams/${team.id}`, { method: "DELETE" }),
    onSuccess: (_, team) => { if (selected?.id === team.id) setSelected(null); refreshTeams(); },
    onError: e => setError(e instanceof Error ? e.message : "Could not delete team")
  });
  const add = useMutation({
    mutationFn: (userId: string) => apiRequest<void>(`/api/v1/organizations/${id}/teams/${selected?.id}/members/${userId}`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["team-members", id, selected?.id] }),
    onError: e => setError(e instanceof Error ? e.message : "Could not add member")
  });
  const removeMember = useMutation({
    mutationFn: (userId: string) => apiRequest<void>(`/api/v1/organizations/${id}/teams/${selected?.id}/members/${userId}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["team-members", id, selected?.id] }),
    onError: e => setError(e instanceof Error ? e.message : "Could not remove member")
  });

  if (!id) return <Navigate to="/setup" replace />;
  function openCreate() { setEditing(null); setName(""); setDescription(""); setModalError(""); setOpen(true); }
  function openEdit(team: Team) { setEditing(team); setName(team.name); setDescription(team.description ?? ""); setModalError(""); setOpen(true); }
  function submit(e: FormEvent) { e.preventDefault(); setModalError(""); editing ? update.mutate() : create.mutate(); }
  const saving = create.isPending || update.isPending;

  return <div>
    <SectionHeading title="Teams" description="Create teams and organize members within your workspace."
      action={<button onClick={openCreate} className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white"><Plus size={15}/>Create team</button>} />
    {error && <p role="alert" className="mb-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {(teams.data ?? []).map(team => <article key={team.id} className={`rounded-xl border bg-white p-5 shadow-sm ${selected?.id === team.id ? "border-indigo-400 ring-2 ring-indigo-100" : "border-slate-200"}`}>
        <button onClick={() => setSelected(team)} className="w-full text-left">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600"><Users size={20}/></div>
          <h2 className="mt-4 text-sm font-semibold text-slate-900">{team.name}</h2>
          <p className="mt-1 min-h-9 text-xs leading-5 text-slate-500">{team.description || "No description"}</p>
          <p className="mt-4 text-xs font-medium text-indigo-600">Manage team members →</p>
        </button>
        <div className="mt-4 flex gap-3 border-t border-slate-100 pt-3">
          <button onClick={() => openEdit(team)} className="inline-flex items-center gap-1 text-xs font-medium text-slate-600"><Pencil size={13}/>Edit</button>
          <button onClick={() => { if (confirm(`Delete team "${team.name}"? Its team assignments will also be removed.`)) remove.mutate(team); }} disabled={remove.isPending} className="inline-flex items-center gap-1 text-xs font-medium text-red-600"><Trash2 size={13}/>Delete</button>
        </div>
      </article>)}
    </div>
    {teams.isLoading && <p className="text-sm text-slate-500">Loading teams…</p>}
    {teams.error && <p role="alert" className="mt-3 text-sm text-red-600">{teams.error instanceof Error ? teams.error.message : "Unable to load teams"}</p>}
    {teams.data?.length === 0 && <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">No teams yet. Create your first team.</p>}

    {selected && <section className="mt-6 rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex items-center justify-between"><div><h2 className="text-sm font-semibold">{selected.name} members</h2><p className="mt-1 text-xs text-slate-500">Add or remove existing organization members.</p></div><button onClick={() => setSelected(null)} className="text-xs text-slate-500">Close</button></div>
      <div className="mt-4 space-y-2">
        {(teamMembers.data ?? []).map(m => <div key={m.user_id} className="flex justify-between rounded-lg bg-slate-50 p-3 text-xs"><span>{m.full_name} · {m.email}</span><button onClick={() => removeMember.mutate(m.user_id)} disabled={removeMember.isPending} className="text-red-600">Remove</button></div>)}
        {teamMembers.isLoading && <p className="text-xs text-slate-500">Loading team members…</p>}
        {teamMembers.data?.length === 0 && <p className="text-xs text-slate-500">No members assigned to this team yet.</p>}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <select id="add-team-member" className="min-w-0 flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs"><option value="">Choose organization member…</option>
          {(members.data ?? []).filter(m => !teamMembers.data?.some(tm => tm.user_id === m.user_id)).map(m => <option key={m.user_id} value={m.user_id}>{m.full_name} ({m.email})</option>)}
        </select>
        <button onClick={() => { const el = document.getElementById("add-team-member") as HTMLSelectElement | null; if (el?.value) add.mutate(el.value); }} disabled={add.isPending} className="rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white">Add member</button>
      </div>
    </section>}

    {open && <div className="fixed inset-0 z-[100] flex items-center justify-center overflow-y-auto bg-slate-950/55 p-3 sm:p-6" onMouseDown={e => { if (e.target === e.currentTarget && !saving) setOpen(false); }}>
      <form role="dialog" aria-modal="true" aria-labelledby="team-form-title" onSubmit={submit} className="my-auto max-h-[92dvh] w-full max-w-md overflow-y-auto overscroll-contain rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl sm:p-6">
        <div className="flex items-center justify-between gap-3"><h2 id="team-form-title" className="text-lg font-semibold">{editing ? "Edit team" : "Create team"}</h2><button type="button" aria-label="Close dialog" onClick={() => setOpen(false)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">✕</button></div>
        {modalError && <p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{modalError}</p>}
        <label className="mt-5 block text-xs font-medium">Team name</label><input required minLength={2} maxLength={120} value={name} onChange={e => setName(e.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm"/>
        <label className="mt-4 block text-xs font-medium">Description</label><textarea maxLength={500} value={description} onChange={e => setDescription(e.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm"/>
        <div className="mt-6 flex justify-end gap-2"><button type="button" onClick={() => setOpen(false)} className="rounded-lg border px-4 py-2 text-xs">Cancel</button><button disabled={saving} className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white">{saving ? "Saving…" : editing ? "Save changes" : "Create team"}</button></div>
      </form>
    </div>}
  </div>;
}
