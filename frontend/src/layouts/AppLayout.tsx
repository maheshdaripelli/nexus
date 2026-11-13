import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { Activity, BarChart3, Bell, ChevronDown, Command, LayoutDashboard, Menu, Search, Settings, ShieldCheck, Users, UsersRound, X } from "lucide-react";
import Avatar from "../components/Avatar";

const links = [
  {to:"/",label:"Overview",icon:LayoutDashboard},
  {to:"/users",label:"Users",icon:Users},
  {to:"/teams",label:"Teams",icon:UsersRound},
  {to:"/roles",label:"Roles & permissions",icon:ShieldCheck},
  {to:"/audit-logs",label:"Audit logs",icon:Activity}
];

export default function AppLayout() {
  const [mobileOpen,setMobileOpen] = useState(false);
  const sidebar = <div className="flex h-full flex-col">
    <div className="flex h-[72px] items-center gap-3 border-b border-slate-200 px-6">
      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white"><Command size={19}/></div>
      <div><p className="text-[15px] font-bold tracking-tight text-slate-900">nexus</p><p className="text-[10px] font-medium uppercase tracking-[.16em] text-slate-400">Workspace OS</p></div>
    </div>
    <div className="px-4 pt-6">
      <button className="flex w-full items-center gap-3 rounded-xl border border-slate-200 p-3 text-left hover:bg-slate-50">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-sm font-bold text-indigo-700">A</div>
        <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-slate-800">Acme Corporation</p><p className="text-xs text-slate-400">Free workspace</p></div><ChevronDown size={15} className="text-slate-400"/>
      </button>
    </div>
    <div className="px-4 pt-7"><p className="px-3 text-[10px] font-semibold uppercase tracking-[.14em] text-slate-400">Workspace</p>
      <nav className="mt-3 space-y-1">{links.map(({to,label,icon:Icon})=><NavLink key={to} to={to} end={to==="/"} onClick={()=>setMobileOpen(false)} className={({isActive})=>`flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition ${isActive?"bg-indigo-50 text-indigo-700":"text-slate-600 hover:bg-slate-50 hover:text-slate-900"}`}><Icon size={17}/>{label}</NavLink>)}</nav>
    </div>
    <div className="mt-auto px-4 pb-5">
      <div className="mb-4 rounded-xl bg-gradient-to-br from-indigo-50 to-violet-50 p-4"><p className="text-xs font-semibold text-indigo-900">Need more power?</p><p className="mt-1 text-xs leading-5 text-indigo-700/80">Upgrade your workspace to unlock advanced controls.</p><button className="mt-3 text-xs font-semibold text-indigo-700 hover:underline">Explore plans →</button></div>
      <NavLink to="/settings" className={({isActive})=>`flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium ${isActive?"bg-indigo-50 text-indigo-700":"text-slate-600 hover:bg-slate-50"}`}><Settings size={17}/>Settings</NavLink>
      <div className="mt-4 flex items-center gap-3 border-t border-slate-100 pt-4"><Avatar initials="MD" color="indigo"/><div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold text-slate-800">Mahesh Daripelli</p><p className="truncate text-[11px] text-slate-400">mahesh@acme.com</p></div><button aria-label="Profile menu"><ChevronDown size={16} className="text-slate-400"/></button></div>
    </div>
  </div>;

  return <div className="min-h-screen bg-[#f7f8fc]">
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-[258px] border-r border-slate-200 bg-white lg:block">{sidebar}</aside>
    {mobileOpen && <div className="fixed inset-0 z-50 lg:hidden"><button aria-label="Close menu" className="absolute inset-0 bg-slate-900/30" onClick={()=>setMobileOpen(false)}/><aside className="absolute inset-y-0 left-0 w-[280px] bg-white shadow-xl">{sidebar}</aside></div>}
    <div className="lg:pl-[258px]">
      <header className="sticky top-0 z-20 flex h-[72px] items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur sm:px-7">
        <div className="flex items-center gap-3"><button className="text-slate-500 lg:hidden" onClick={()=>setMobileOpen(true)} aria-label="Open menu"><Menu size={21}/></button><div className="hidden items-center gap-2 text-xs text-slate-400 sm:flex"><span>Workspace</span><span>/</span><span className="font-medium text-slate-700">Overview</span></div><span className="text-sm font-semibold text-slate-800 sm:hidden">Nexus</span></div>
        <div className="flex items-center gap-2 sm:gap-4"><button className="hidden h-9 items-center gap-2 rounded-lg border border-slate-200 px-3 text-xs text-slate-400 md:flex"><Search size={14}/>Search anything <kbd className="ml-5 rounded border border-slate-200 px-1.5 py-0.5 text-[10px]">⌘ K</kbd></button><button aria-label="Notifications" className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-50"><Bell size={18}/><span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-indigo-600 ring-2 ring-white"/></button><div className="hidden h-6 w-px bg-slate-200 sm:block"/><Avatar initials="MD" color="indigo" size="sm"/></div>
      </header>
      <main className="mx-auto max-w-[1440px] px-4 py-7 sm:px-7 lg:px-9"><Outlet/></main>
      <footer className="px-7 pb-6 text-center text-[11px] text-slate-400">© 2025 Nexus Workspace. Built for teams that move forward.</footer>
    </div>
  </div>;
}
