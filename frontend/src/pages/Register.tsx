import { Navigate } from "react-router-dom";

// Public self-registration is disabled. Accounts are created through valid invitations.
export default function RegisterPage() {
  return <Navigate to="/login" replace />;
}
