import { Plus, Users } from "lucide-react";
import SectionHeading from "../components/SectionHeading";
import Avatar from "../components/Avatar";
import { teams } from "../data/demo";

const teamColors:Record<string,string> = {
  blue:"bg-blue-50 text-blue-600", violet:"bg-violet-50 text-violet-600",
  pink:"bg-pink-50 text-pink-600", orange:"bg-orange-50 text-orange-600",
  green:"bg-emerald-50 text-emerald-600"
};

export default function TeamsPage() {
  return <div><SectionHeading title="Teams" description="Organize your people into focused groups." action={<button className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white"><Plus size={15}/>Create team</button>}/><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{teams.map(team=><div key={team.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between"><div className={`flex h-11 w-11 items-center justify-center rounded-xl ${teamColors[team.color] ?? teamColors.blue}`}><Users size={20}/></div><button className="text-slate-400">•••</button></div><h2 className="mt-4 text-sm font-semibold text-slate-900">{team.name}</h2><p className="mt-1 min-h-9 text-xs leading-5 text-slate-500">{team.description}</p><div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4"><div className="flex -space-x-2"><Avatar initials="OR" color="violet" size="sm"/><Avatar initials="PB" color="orange" size="sm"/><Avatar initials="LS" color="pink" size="sm"/></div><span className="text-xs text-slate-500">{team.members} members</span></div><p className="mt-3 text-[11px] text-slate-400">Team lead: <span className="font-medium text-slate-600">{team.lead}</span></p></div>)}</div></div>;
}
