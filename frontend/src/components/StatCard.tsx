import type { LucideIcon } from "lucide-react";
type Props = { title:string; value:string; change:string; note:string; icon:LucideIcon; positive?:boolean };
export default function StatCard({title,value,change,note,icon:Icon,positive=true}:Props) {
  return <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
    <div className="flex items-start justify-between"><p className="text-sm font-medium text-slate-500">{title}</p><span className="rounded-lg bg-slate-50 p-2 text-slate-500"><Icon size={18}/></span></div>
    <div className="mt-4 flex items-baseline gap-2"><p className="text-3xl font-semibold tracking-tight text-slate-900">{value}</p><span className={`text-xs font-semibold ${positive?"text-emerald-600":"text-rose-600"}`}>{change}</span></div>
    <p className="mt-1 text-xs text-slate-500">{note}</p>
  </div>;
}
