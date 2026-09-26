import { Navigate } from "react-router-dom";
import type { UserPublic } from "@/lib/types";

export const routeForRole = (role: UserPublic["role"]) =>
  role === "OFFICER" ? "/control-room" : role === "RESPONSE_TEAM" ? "/team" : "/civilian";

export default function RoleLanding() {
  if (import.meta.env.PROD) {
    const raw = localStorage.getItem("kiit-demo-user");

    if (!raw) return <Navigate to="/login" replace />;

    try {
      const user = JSON.parse(raw) as UserPublic;
      return <Navigate to={routeForRole(user.role)} replace />;
    } catch {
      localStorage.removeItem("kiit-demo-user");
      return <Navigate to="/login" replace />;
    }
  }

  return <Navigate to="/login" replace />;
}
