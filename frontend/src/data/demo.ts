import type { Role, Team, User } from "../types";

export const users: User[] = [
  { id:"USR-001", name:"Olivia Rhye", email:"olivia@acme.com", role:"Admin", team:"Engineering", status:"Active", joined:"Jan 12, 2025", initials:"OR", color:"violet" },
  { id:"USR-002", name:"Phoenix Baker", email:"phoenix@acme.com", role:"Manager", team:"Design", status:"Active", joined:"Feb 03, 2025", initials:"PB", color:"orange" },
  { id:"USR-003", name:"Lana Steiner", email:"lana@acme.com", role:"Member", team:"Product", status:"Active", joined:"Feb 18, 2025", initials:"LS", color:"pink" },
  { id:"USR-004", name:"Demi Wilkinson", email:"demi@acme.com", role:"Member", team:"Engineering", status:"Invited", joined:"Mar 02, 2025", initials:"DW", color:"blue" },
  { id:"USR-005", name:"Candice Wu", email:"candice@acme.com", role:"Manager", team:"Marketing", status:"Active", joined:"Mar 11, 2025", initials:"CW", color:"green" },
  { id:"USR-006", name:"Natali Craig", email:"natali@acme.com", role:"Member", team:"Design", status:"Suspended", joined:"Apr 06, 2025", initials:"NC", color:"cyan" },
  { id:"USR-007", name:"Drew Cano", email:"drew@acme.com", role:"Member", team:"Engineering", status:"Active", joined:"Apr 21, 2025", initials:"DC", color:"amber" },
  { id:"USR-008", name:"Orlando Diggs", email:"orlando@acme.com", role:"Viewer", team:"Sales", status:"Active", joined:"May 09, 2025", initials:"OD", color:"indigo" }
];

export const teams: Team[] = [
  { id:"TEAM-01", name:"Engineering", description:"Build and maintain the product", members:18, lead:"Olivia Rhye", color:"blue" },
  { id:"TEAM-02", name:"Design", description:"Create delightful user experiences", members:8, lead:"Phoenix Baker", color:"violet" },
  { id:"TEAM-03", name:"Product", description:"Shape the product roadmap", members:6, lead:"Lana Steiner", color:"pink" },
  { id:"TEAM-04", name:"Marketing", description:"Grow awareness and demand", members:9, lead:"Candice Wu", color:"orange" },
  { id:"TEAM-05", name:"Sales", description:"Build customer relationships", members:7, lead:"Orlando Diggs", color:"green" }
];

export const roles: Role[] = [
  { id:"ROLE-01", name:"Owner", description:"Full access to workspace settings and data", users:1, permissions:["All permissions"] },
  { id:"ROLE-02", name:"Admin", description:"Manage users, teams, roles and workspace", users:3, permissions:["Manage users","Manage teams","View audit logs","Manage settings"] },
  { id:"ROLE-03", name:"Manager", description:"Manage assigned teams and their members", users:8, permissions:["View users","Manage team members","View reports"] },
  { id:"ROLE-04", name:"Member", description:"Standard access to workspace resources", users:32, permissions:["View workspace","Edit own profile"] },
  { id:"ROLE-05", name:"Viewer", description:"Read-only access to workspace resources", users:4, permissions:["View workspace","View reports"] }
];

export const activity = [
  { name:"Olivia Rhye", action:"updated workspace settings", time:"12 minutes ago", initials:"OR", color:"violet" },
  { name:"Phoenix Baker", action:"invited demi@acme.com", time:"1 hour ago", initials:"PB", color:"orange" },
  { name:"Candice Wu", action:"created the Marketing team", time:"3 hours ago", initials:"CW", color:"green" },
  { name:"Lana Steiner", action:"changed a member's role", time:"Yesterday", initials:"LS", color:"pink" }
];

export const chartData = [
  { month:"Jan", users:24, active:18 }, { month:"Feb", users:32, active:25 },
  { month:"Mar", users:29, active:23 }, { month:"Apr", users:45, active:36 },
  { month:"May", users:52, active:42 }, { month:"Jun", users:61, active:49 },
  { month:"Jul", users:58, active:47 }, { month:"Aug", users:73, active:59 },
  { month:"Sep", users:82, active:68 }, { month:"Oct", users:91, active:76 },
  { month:"Nov", users:105, active:89 }, { month:"Dec", users:118, active:101 }
];
