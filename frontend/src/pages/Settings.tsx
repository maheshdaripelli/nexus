import { type FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Navigate } from "react-router-dom";
import SectionHeading from "../components/SectionHeading";
import { useAuth } from "../auth/AuthContext";
import { apiRequest } from "../lib/api";
type Organization={id:string;name:string;slug:string;created_at:string};

export default function SettingsPage(){
 const id=localStorage.getItem("nexus.organization_id");
 const qc=useQueryClient();
 const {user,updateProfile}=useAuth();
 const [profileName,setProfileName]=useState(user?.full_name??"");
 const [workspaceName,setWorkspaceName]=useState("");
 const [profileError,setProfileError]=useState("");
 const [profileSuccess,setProfileSuccess]=useState("");
 const [workspaceError,setWorkspaceError]=useState("");
 const [workspaceSuccess,setWorkspaceSuccess]=useState("");
 const org=useQuery({queryKey:["organizations",id],enabled:!!id,queryFn:async()=>{const items=await apiRequest<Organization[]>("/api/v1/organizations");return items.find(x=>x.id===id)??null;}});
 useEffect(()=>{if(user)setProfileName(user.full_name);},[user]);
 useEffect(()=>{if(org.data)setWorkspaceName(org.data.name);},[org.data]);
 const profileUpdate=useMutation({mutationFn:()=>updateProfile(profileName.trim()),onSuccess:()=>{setProfileSuccess("Profile updated successfully.");setProfileError("");},onError:e=>setProfileError(e instanceof Error?e.message:"Could not update profile")});
 const workspaceUpdate=useMutation({mutationFn:()=>apiRequest<Organization>("/api/v1/organizations/"+id,{method:"PATCH",body:JSON.stringify({name:workspaceName.trim()})}),onSuccess:result=>{setWorkspaceSuccess("Workspace name updated.");setWorkspaceError("");qc.invalidateQueries({queryKey:["organizations"]});qc.setQueryData(["organizations",id],result);},onError:e=>setWorkspaceError(e instanceof Error?e.message:"Could not update workspace")});
 if(!id)return <Navigate to="/setup" replace/>;
 function saveProfile(e:FormEvent){e.preventDefault();setProfileError("");setProfileSuccess("");profileUpdate.mutate();}
 function saveWorkspace(e:FormEvent){e.preventDefault();setWorkspaceError("");setWorkspaceSuccess("");workspaceUpdate.mutate();}
 return <div>
  <SectionHeading title="Settings" description="Manage your personal profile and organization workspace."/>
  <div className="grid max-w-4xl gap-5">
   <form onSubmit={saveProfile} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
    <h2 className="text-sm font-semibold text-slate-900">Personal profile</h2>
    <p className="mt-1 text-xs text-slate-500">Update the name shown across your Nexus workspaces.</p>
    {profileError&&<p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{profileError}</p>}
    {profileSuccess&&<p role="status" className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{profileSuccess}</p>}
    <label className="mt-5 block text-xs font-medium text-slate-700">Full name</label>
    <input required minLength={2} maxLength={120} value={profileName} onChange={e=>{setProfileName(e.target.value);setProfileSuccess("");}} className="mt-2 w-full max-w-md rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-400"/>
    <label className="mt-4 block text-xs font-medium text-slate-700">Email address</label>
    <input disabled value={user?.email??""} className="mt-2 w-full max-w-md rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-500"/>
    <p className="mt-2 text-[11px] text-slate-400">Your sign-in email cannot be changed here.</p>
    <button disabled={profileUpdate.isPending||!profileName.trim()} className="mt-6 rounded-lg bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white disabled:opacity-60">{profileUpdate.isPending?"Saving…":"Save profile"}</button>
   </form>
   <form onSubmit={saveWorkspace} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
    <h2 className="text-sm font-semibold text-slate-900">Workspace settings</h2>
    <p className="mt-1 text-xs text-slate-500">Manage the organization details for the currently selected workspace.</p>
    {workspaceError&&<p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{workspaceError}</p>}
    {workspaceSuccess&&<p role="status" className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{workspaceSuccess}</p>}
    <label className="mt-5 block text-xs font-medium text-slate-700">Workspace name</label>
    <input required minLength={2} maxLength={160} value={workspaceName} onChange={e=>{setWorkspaceName(e.target.value);setWorkspaceSuccess("");}} className="mt-2 w-full max-w-md rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-400"/>
    <p className="mt-2 text-[11px] text-slate-400">Only users with the workspace.manage permission can save changes.</p>
    <button disabled={workspaceUpdate.isPending||org.isLoading||!workspaceName.trim()} className="mt-6 rounded-lg bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white disabled:opacity-60">{workspaceUpdate.isPending?"Saving…":"Save workspace"}</button>
   </form>
  </div>
 </div>;
}