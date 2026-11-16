import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Navigate } from "react-router-dom";
import SectionHeading from "../components/SectionHeading";
import { apiRequest } from "../lib/api";
type Organization={id:string;name:string;slug:string;created_at:string};
export default function SettingsPage(){
 const id=localStorage.getItem("nexus.organization_id");const qc=useQueryClient();const [name,setName]=useState("");const [error,setError]=useState("");const [success,setSuccess]=useState("");
 const org=useQuery({queryKey:["organizations",id],enabled:!!id,queryFn:async()=>{const items=await apiRequest<Organization[]>("/api/v1/organizations");return items.find(x=>x.id===id)??null;}});
 useEffect(()=>{if(org.data)setName(org.data.name);},[org.data]);
 const update=useMutation({mutationFn:()=>apiRequest<Organization>("/api/v1/organizations/"+id,{method:"PATCH",body:JSON.stringify({name})}),onSuccess:result=>{setSuccess("Workspace name updated.");setError("");qc.invalidateQueries({queryKey:["organizations"]});qc.setQueryData(["organizations",id],result);},onError:e=>setError(e instanceof Error?e.message:"Could not update workspace")});
 if(!id)return <Navigate to="/setup" replace/>;
 function submit(e:FormEvent){e.preventDefault();setError("");setSuccess("");update.mutate();}
 return <div><SectionHeading title="Settings" description="Manage your organization workspace details."/><form onSubmit={submit} className="max-w-3xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-sm font-semibold text-slate-900">General settings</h2><p className="mt-1 text-xs text-slate-500">These details are stored in your Nexus organization record.</p>{error&&<p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}{success&&<p className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{success}</p>}<label className="mt-6 block text-xs font-medium text-slate-700">Workspace name</label><input required minLength={2} maxLength={160} value={name} onChange={e=>{setName(e.target.value);setSuccess("");}} className="mt-2 w-full max-w-md rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-400"/><p className="mt-2 text-[11px] text-slate-400">The current backend does not yet persist timezone or other preference settings.</p><button disabled={update.isPending||org.isLoading} className="mt-6 rounded-lg bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white disabled:opacity-60">{update.isPending?"Saving…":"Save changes"}</button></form></div>;
}
