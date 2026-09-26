import { Routes, Route } from "react-router-dom";
import { Navigate } from "react-router-dom";
import Auth from "@/pages/Auth";
import ControlRoom from "@/pages/ControlRoom";
import CivilianDashboard from "@/pages/CivilianDashboard";
import RoleLanding from "@/pages/RoleLanding";
import TeamDashboard from "@/pages/TeamDashboard";

// One <Route> per page in src/pages; BrowserRouter already wraps this in main.tsx.
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RoleLanding />} />
      <Route path="/login" element={<Auth />} />
      <Route path="/civilian" element={<CivilianDashboard />} />
      <Route path="/control-room" element={<ControlRoom />} />
      <Route path="/team" element={<TeamDashboard />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
