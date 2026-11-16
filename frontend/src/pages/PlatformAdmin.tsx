import { useQuery } from "@tanstack/react-query";
import { Building2, Users, UserRound } from "lucide-react";
import SectionHeading from "../components/SectionHeading";
import { apiRequest } from "../lib/api";
type Overview={organization_count:number;user_count:number;membership_count:number};
type Organization={id:string;name:string;slug:string;created_at:string;member_count:number};
export default function PlatformAdminPage(){
 const overview=useQuery({queryKey:["platform-overview"],queryFn:()=>apiRequest<Overview>("/api/v1/platform/overview")});
 const organizations=useQuery({queryKey:["platform-organizations"],queryFn:()=>apiRequest<Organization[]>("/api/v1/platform/organizations")});
 const error=overview.error??organizations.error;
 return <div><SectionHeading title="Platform administration" description="Global Nexus operations. This area is separate from organization-level administration."/>
 {error&&<div role="alert" className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700">{error instanceof Error?error.message:"Platform administrator access is required."}</div>}
 <div className="grid gap-4 sm:grid-cols-3"><div className="rounded-xl border bg-white p-5"><Building2 className="text-indigo-600"/><p className="mt-3 text-xs text-slate-500">Organizations</p><p className="mt-1 text-2xl font-semibold">{overview.data?.organization_count??"—"}</p></div><div className="rounded-xl border bg-white p-5"><Users className="text-indigo-600"/><p className="mt-3 text-xs text-slate-500">Global users</p><p className="mt-1 text-2xl font-semibold">{overview.data?.user_count??"—"}</p></div><div className="rounded-xl border bg-white p-5"><UserRound className="text-indigo-600"/><p className="mt-3 text-xs text-slate-500">Memberships</p><p className="mt-1 text-2xl font-semibold">{overview.data?.membership_count??"—"}</p></div></div>
 <section className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white"><div className="border-b p-5"><h2 className="text-sm font-semibold">All organizations</h2><p className="mt-1 text-xs text-slate-500">Global organization directory across Nexus.</p></div><div className="overflow-x-auto"><table className="w-full min-w-[600px] text-left"><thead className="bg-slate-50 text-[10px] uppercase text-slate-400"><tr><th className="px-5 py-3">Organization</th><th className="px-5 py-3">Slug</th><th className="px-5 py-3">Members</th><th className="px-5 py-3">Created</th></tr></thead><tbody className="divide-y">{(organizations.data??[]).map(o=><tr key={o.id}><td className="px-5 py-4 text-xs font-semibold">{o.name}</td><td className="px-5 py-4 text-xs text-slate-500">{o.slug}</td><td className="px-5 py-4 text-xs">{o.member_count}</td><td className="px-5 py-4 text-xs text-slate-500">{new Date(o.created_at).toLocaleDateString()}</td></tr>)}</tbody></table>{organizations.isLoading&&<p className="p-5 text-sm text-slate-500">Loading organizations…</p>}</div></section>
 </div>;
}
