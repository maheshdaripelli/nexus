import type { UserStatus } from "../types";
export default function Badge({status}:{status:UserStatus|string}) {
  const styles:Record<string,string> = {
    Active:"bg-emerald-50 text-emerald-700 ring-emerald-600/20",
    Invited:"bg-amber-50 text-amber-700 ring-amber-600/20",
    Suspended:"bg-rose-50 text-rose-700 ring-rose-600/20"
  };
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${styles[status] ?? "bg-slate-100 text-slate-600 ring-slate-500/20"}`}><span className="h-1.5 w-1.5 rounded-full bg-current"/>{status}</span>;
}
