type Props = { initials: string; color?: string; size?: "sm" | "md" | "lg" };
const colors: Record<string,string> = {
  violet:"bg-violet-100 text-violet-700", orange:"bg-orange-100 text-orange-700",
  pink:"bg-pink-100 text-pink-700", blue:"bg-blue-100 text-blue-700",
  green:"bg-emerald-100 text-emerald-700", cyan:"bg-cyan-100 text-cyan-700",
  amber:"bg-amber-100 text-amber-700", indigo:"bg-indigo-100 text-indigo-700"
};
export default function Avatar({initials,color="blue",size="md"}:Props) {
  const dimensions = size === "sm" ? "h-8 w-8 text-[10px]" : size === "lg" ? "h-12 w-12 text-sm" : "h-10 w-10 text-xs";
  return <div className={`${dimensions} ${colors[color] ?? colors.blue} flex shrink-0 items-center justify-center rounded-full font-semibold`}>{initials}</div>;
}
