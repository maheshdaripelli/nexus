import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Activity, ChevronDown, Command, LayoutDashboard, LogOut, Menu, Search, Settings, ShieldCheck, Users, UsersRound, UserCircle, Building2 } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import Avatar from "../components/Avatar";
import { apiRequest } from "../lib/api";

const links=[
 {to:"/",label:"Overview",icon:LayoutDashboard,keywords:"dashboard home stats"},
 {to:"/users",label:"Users",icon:Users,keywords:"members people invitations"},
 {to:"/teams",label:"Teams",icon:UsersRound,keywords:"groups team members"},
 {to:"/roles",label:"Roles & permissions",icon:ShieldCheck,keywords:"rbac access permissions"},
 {to:"/audit-logs",label:"Audit logs",icon:Activity,keywords:"history activity events"},
 {to:"/settings",label:"Settings",icon:Settings,keywords:"workspace organization preferences"}
];
type Organization={id:string;name:string;slug:string;created_at:string};

export default function AppLayout(){
 const [mobileOpen,setMobileOpen]=useState(false);
 const [search,setSearch]=useState("");
 const [profileOpen,setProfileOpen]=useState(false);
 const {user,logout}=useAuth();
 const navigate=useNavigate();
 const organizationId=localStorage.getItem("nexus.organization_id");
 const organizations=useQuery({queryKey:["organizations"],queryFn:()=>apiRequest<Organization[]>("/api/v1/organizations")});
 const organizationName=organizations.data?.find(org=>org.id===organizationId)?.name??"Your workspace";
 const initials=(user?.full_name??"U").split(" ").map(x=>x[0]).join("").slice(0,2).toUpperCase();
 const filteredLinks=links.filter(link=>(link.label+" "+link.keywords).toLowerCase().includes(search.toLowerCase()));
 async function signOut(){try{await logout();}finally{localStorage.removeItem("nexus.organization_id");navigate("/login",{replace:true});}}
 function go(to:string){navigate(to);setSearch("");setProfileOpen(false);setMobileOpen(false);}
 const sidebar=<div className="flex h-full flex-col">
  <div className="flex h-[72px] items-center gap-3 border-b border-slate-200 px-6"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white"><Command size={19}/></div><div><p className="text-[15px] font-bold tracking-tight text-slate-900">nexus</p><p className="text-[10px] font-medium uppercase tracking-[.16em] text-slate-400">Workspace OS</p></div></div>
  <div className="px-4 pt-6"><button onClick={()=>go("/setup")} className="flex w-full items-center gap-3 rounded-xl border border-slate-200 p-3 text-left hover:bg-slate-50"><div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-sm font-bold text-indigo-700">{organizationName.slice(0,1).toUpperCase()}</div><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-slate-800">{organizationName}</p><p className="text-xs text-slate-400">Switch workspace</p></div><ChevronDown size={15} className="text-slate-400"/></button></div>
  <div className="px-4 pt-7"><p className="px-3 text-[10px] font-semibold uppercase tracking-[.14em] text-slate-400">Workspace</p><nav className="mt-3 space-y-1">{links.filter(l=>l.to!=="/settings").map(({to,label,icon:Icon})=><NavLink key={to} to={to} end={to==="/"} onClick={()=>setMobileOpen(false)} className={({isActive})=>`flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition ${isActive?"bg-indigo-50 text-indigo-700":"text-slate-600 hover:bg-slate-50 hover:text-slate-900"}`}><Icon size={17}/>{label}</NavLink>)}</nav></div>
  <div className="mt-auto px-4 pb-5"><NavLink to="/platform" className={({isActive})=>`flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium ${isActive?"bg-indigo-50 text-indigo-700":"text-slate-600 hover:bg-slate-50"}`}><ShieldCheck size={17}/>Platform admin</NavLink><NavLink to="/settings" className={({isActive})=>`flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium ${isActive?"bg-indigo-50 text-indigo-700":"text-slate-600 hover:bg-slate-50"}`}><Settings size={17}/>Settings</NavLink><div className="mt-4 flex items-center gap-3 border-t border-slate-100 pt-4"><Avatar initials={initials} color="indigo"/><div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold text-slate-800">{user?.full_name}</p><p className="truncate text-[11px] text-slate-400">{user?.email}</p></div><button aria-label="Sign out" title="Sign out" onClick={signOut} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><LogOut size={16}/></button></div></div>
 </div>;
 return <div className="min-h-screen bg-[#f7f8fc]"><aside className="fixed inset-y-0 left-0 z-30 hidden w-[258px] border-r border-slate-200 bg-white lg:block">{sidebar}</aside>
 {mobileOpen&&<div className="fixed inset-0 z-50 lg:hidden"><button aria-label="Close menu" className="absolute inset-0 bg-slate-900/30" onClick={()=>setMobileOpen(false)}/><aside className="absolute inset-y-0 left-0 w-[280px] bg-white shadow-xl">{sidebar}</aside></div>}
 <div className="lg:pl-[258px]"><header className="sticky top-0 z-20 flex h-[72px] items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-7"><div className="flex items-center gap-3"><button className="text-slate-500 lg:hidden" onClick={()=>setMobileOpen(true)} aria-label="Open menu"><Menu size={21}/></button><span className="text-sm font-semibold text-slate-800">Nexus workspace</span></div>
 <div className="flex items-center gap-3"><div className="relative hidden md:block"><div className="flex h-9 w-64 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 focus-within:border-indigo-400"><Search size={14} className="shrink-0 text-slate-400"/><input aria-label="Search Nexus pages" value={search} onChange={e=>setSearch(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&filteredLinks[0])go(filteredLinks[0].to);if(e.key==="Escape")setSearch("");}} placeholder="Search pages…" className="w-full bg-transparent text-xs outline-none placeholder:text-slate-400"/><kbd className="text-[10px] text-slate-400">↵</kbd></div>{search&&<div className="absolute right-0 top-11 z-40 w-64 overflow-hidden rounded-xl border border-slate-200 bg-white p-1 shadow-lg">{filteredLinks.length?filteredLinks.map(({to,label,icon:Icon})=><button key={to} onClick={()=>go(to)} className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-xs text-slate-700 hover:bg-indigo-50"><Icon size={15}/>{label}</button>):<p className="p-3 text-xs text-slate-500">No matching pages found.</p>}</div>}</div>
 <div className="relative"><button aria-label="Open profile menu" aria-expanded={profileOpen} onClick={()=>setProfileOpen(v=>!v)} className="flex items-center gap-2 rounded-full p-1 hover:bg-slate-100"><Avatar initials={initials} color="indigo" size="sm"/><ChevronDown size={14} className="text-slate-500"/></button>{profileOpen&&<div className="absolute right-0 top-11 z-40 w-60 rounded-xl border border-slate-200 bg-white p-2 shadow-lg"><div className="border-b border-slate-100 px-3 py-2"><p className="truncate text-xs font-semibold text-slate-800">{user?.full_name}</p><p className="truncate text-[11px] text-slate-500">{user?.email}</p></div><button onClick={()=>go("/settings")} className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-xs text-slate-700 hover:bg-slate-50"><UserCircle size={15}/>Account & workspace settings</button><button onClick={()=>go("/setup")} className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-xs text-slate-700 hover:bg-slate-50"><Building2 size={15}/>Switch workspace</button><button onClick={signOut} className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-xs text-red-600 hover:bg-red-50"><LogOut size={15}/>Sign out</button></div>}</div></div></header>
 <main className="mx-auto max-w-[1440px] px-4 py-7 sm:px-7 lg:px-9"><Outlet/></main><footer className="px-7 pb-6 text-center text-[11px] text-slate-400">Nexus · Workspace management</footer></div></div>;
}
