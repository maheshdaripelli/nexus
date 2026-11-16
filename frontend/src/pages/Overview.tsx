import { useQuery } from "@tanstack/react-query";
import { Activity, Building2, Users, UsersRound } from "lucide-react";
import { Link, Navigate } from "react-router-dom";
import SectionHeading from "../components/SectionHeading";
import StatCard from "../components/StatCard";
import { apiRequest } from "../lib/api";

type Stats={organization_id:string;member_count:number;team_count:number};
function orgId(){return localStorage.getItem("nexus.organization_id");}
export default function Overview(){
 const id=orgId();
 const {data,error,isLoading}=useQuery({queryKey:["dashboard",id],enabled:!!id,queryFn:()=>apiRequest<Stats>(`/api/v1/organizations/${id}/dashboard/stats`)});
 if(!id)return <Navigate to="/setup" replace/>;
 return <div><SectionHeading title="Workspace overview" description="Live statistics from your Nexus organization."/>
 {error&&<p role="alert" className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error instanceof Error?error.message:"Unable to load dashboard"}</p>}
 {isLoading?<p className="text-sm text-slate-500">Loading workspace statistics…</p>:<div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"><StatCard title="Organization members" value={String(data?.member_count??0)} change="Live" note="Current organization membership" icon={Users}/><StatCard title="Teams" value={String(data?.team_count??0)} change="Live" note="Teams in this workspace" icon={UsersRound}/><StatCard title="Workspace" value="Active" change="Connected" note="Statistics loaded from the API" icon={Building2}/></div>}
 <div className="mt-6 grid gap-4 md:grid-cols-2"><Link to="/users" className="rounded-xl border border-slate-200 bg-white p-5 hover:border-indigo-300"><Users className="text-indigo-600"/><h2 className="mt-3 text-sm font-semibold text-slate-900">Manage members</h2><p className="mt-1 text-xs text-slate-500">View members, change roles and invite colleagues.</p></Link><Link to="/teams" className="rounded-xl border border-slate-200 bg-white p-5 hover:border-indigo-300"><UsersRound className="text-indigo-600"/><h2 className="mt-3 text-sm font-semibold text-slate-900">Manage teams</h2><p className="mt-1 text-xs text-slate-500">Create teams and assign organization members.</p></Link></div>
 <p className="mt-6 text-xs text-slate-400"><Activity size={13} className="mr-1 inline"/> Dashboard values are fetched from the Nexus API, not demo fixtures.</p></div>;
}
