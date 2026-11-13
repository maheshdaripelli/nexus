import { Activity, Download } from "lucide-react";
import SectionHeading from "../components/SectionHeading";
import Avatar from "../components/Avatar";
import { activity } from "../data/demo";

const logs = [...activity,{name:"Drew Cano",action:"exported the members list",time:"2 days ago",initials:"DC",color:"amber"},{name:"Olivia Rhye",action:"added a new role: Viewer",time:"3 days ago",initials:"OR",color:"violet"}];
export default function AuditLogsPage() {
  return <div><SectionHeading title="Audit logs" description="A record of important actions taken across your workspace." action={<button className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700"><Download size={14}/>Export logs</button>}/><div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="mb-5 flex items-center gap-2"><Activity size={17} className="text-indigo-600"/><h2 className="text-sm font-semibold text-slate-900">Recent events</h2></div><div className="space-y-0">{logs.map((log,i)=><div key={i} className="relative flex gap-3 pb-6 last:pb-0"><div className="relative"><Avatar initials={log.initials} color={log.color} size="sm"/>{i!==logs.length-1&&<span className="absolute left-1/2 top-10 h-full w-px -translate-x-1/2 bg-slate-100"/>}</div><div className="flex-1 pt-1"><p className="text-xs text-slate-700"><span className="font-semibold text-slate-900">{log.name}</span> {log.action}</p><p className="mt-1 text-[11px] text-slate-400">{log.time}</p></div><span className="hidden rounded-md bg-slate-50 px-2 py-1 text-[10px] text-slate-500 sm:block">Workspace</span></div>)}</div></div></div>;
}
