export type UserStatus = "Active" | "Invited" | "Suspended";
export type User = {
  id: string; name: string; email: string; role: string; team: string;
  status: UserStatus; joined: string; initials: string; color: string;
};
export type Team = { id: string; name: string; description: string; members: number; lead: string; color: string };
export type Role = { id: string; name: string; description: string; users: number; permissions: string[] };
