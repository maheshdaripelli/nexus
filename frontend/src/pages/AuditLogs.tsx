import { useQuery } from "@tanstack/react-query";
import { Activity } from "lucide-react";
import { Navigate } from "react-router-dom";
import SectionHeading from "../components/SectionHeading";
import { apiRequest } from "../lib/api";
type Log={id:string;actor_user_id:string|null;action:string;resource_type:string;resource_id:string|null;details:Record<string,unknown>|null;ip_address:string|null;created_at:string};
export default function AuditLogsPage(){
 const id=localStorage.getItem("nexus.organization_id");
 const logs=useQuery({queryKey:["audit-logs",id],enabled:!!id,queryFn:()=>apiRequest<Log[]>("/api/v1/organizations/"+id+"/audit-logs?limit=100&offset=0")});
 if(!id)return <Navigate to="/setup" replace/>;
 return <div><SectionHeading title="Audit logs" description="Review recorded events for your organization."/><div className="rounded-xl border border-slate-200 bg-white p-5"><div className="mb-5 flex items-center gap-2"><Activity size={17} className="text-indigo-600"/><h2 className="text-sm font-semibold">Recorded events</h2></div>{logs.isLoading&&<p className="text-sm text-slate-500">Loading audit events…</p>}{logs.error&&<p role="alert" className="text-sm text-red-600">{logs.error instanceof Error?logs.error.message:"Unable to load audit logs"}</p>}{logs.data?.length===0&&<p className="rounded-lg bg-slate-50 p-6 text-center text-sm text-slate-500">No audit events have been recorded yet. The current backend does not automatically write audit events for every mutation.</p>}<div className="divide-y divide-slate-100">{(logs.data??[]).map(log=><div key={log.id} className="py-4"><p className="text-xs font-semibold text-slate-800">{log.action}</p><p className="mt-1 text-xs text-slate-500">{log.resource_type}{log.resource_id?" · "+log.resource_id:""}</p><p className="mt-1 text-[11px] text-slate-400">{new Date(log.created_at).toLocaleString()} · Actor: {log.actor_user_id??"System"}</p></div>)}</div></div></div>;
}
