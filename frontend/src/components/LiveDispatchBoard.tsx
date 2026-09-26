import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, AlertTriangle, Check, ChevronRight, Clock3, MapPin, Radio, Route, ShieldCheck, Sparkles, Users, X } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import IncidentComms from "@/components/IncidentComms";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { useDispatchEvents } from "@/lib/useDispatchEvents";
import type { IncidentReport, ResponseTeam, TeamRecommendation } from "@/lib/types";

const statusTone: Record<IncidentReport["status"], string> = {
  NEW: "border-blue-200 bg-blue-50 text-blue-700",
  ACKNOWLEDGED: "border-amber-200 bg-amber-50 text-amber-700",
  TEAM_ASSIGNED: "border-orange-200 bg-orange-50 text-orange-700",
  TEAM_ACCEPTED: "border-cyan-200 bg-cyan-50 text-cyan-700",
  EN_ROUTE: "border-purple-200 bg-purple-50 text-purple-700",
  RESOLVED: "border-green-200 bg-green-50 text-green-700",
};

export default function LiveDispatchBoard() {
  const queryClient = useQueryClient();
  const eventsConnected = useDispatchEvents();
  const [selected, setSelected] = useState<IncidentReport | null>(null);
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);
  const [primaryTeam, setPrimaryTeam] = useState("");
  const reports = useQuery({ queryKey: ["dispatch", "reports"], queryFn: ({ signal }) => apiGet<IncidentReport[]>("/dispatch/reports", signal), retry: false, refetchInterval: 10000 });
  const teams = useQuery({ queryKey: ["dispatch", "teams"], queryFn: ({ signal }) => apiGet<ResponseTeam[]>("/dispatch/teams", signal), retry: false, refetchInterval: 15000 });
  const recommendations = useQuery({ queryKey: ["dispatch", "recommendations", selected?.id], queryFn: ({ signal }) => apiGet<TeamRecommendation[]>(`/dispatch/reports/${selected?.id}/recommendations`, signal), enabled: Boolean(selected), retry: false });
  const sortedReports = useMemo(() => [...(reports.data ?? [])].sort((a, b) => Number(a.status === "RESOLVED") - Number(b.status === "RESOLVED") || new Date(b.created_at).getTime() - new Date(a.created_at).getTime()), [reports.data]);
  useEffect(() => { if (selected) { const current = reports.data?.find((report) => report.id === selected.id); if (current) setSelected(current); } }, [reports.data, selected?.id]);
  useEffect(() => { setSelectedTeams(selected?.assigned_team_ids ?? []); setPrimaryTeam(selected?.primary_team_id ?? ""); }, [selected?.id]);

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["dispatch", "reports"] });
    queryClient.invalidateQueries({ queryKey: ["dispatch", "teams"] });
    queryClient.invalidateQueries({ queryKey: ["dispatch", "recommendations"] });
  };
  const acknowledge = useMutation({ mutationFn: (id: string) => apiPatch<IncidentReport>(`/dispatch/reports/${id}/status`, { status: "ACKNOWLEDGED", note: "Control room validated the report and started dispatch review" }), onSuccess: () => { refresh(); toast.success("Incident acknowledged"); } });
  const assign = useMutation({ mutationFn: ({ id, teamIds, primary }: { id: string; teamIds: string[]; primary: string }) => apiPost<IncidentReport>(`/dispatch/reports/${id}/assign`, { team_ids: teamIds, primary_team_id: primary, note: "Teams selected using capability, proximity and workload recommendations" }), onSuccess: () => { refresh(); toast.success("Hero team dispatched — awaiting confirmation"); }, onError: () => toast.error("Select at least one team and a primary responder") });
  const escalate = useMutation({ mutationFn: (id: string) => apiPost<IncidentReport>(`/dispatch/reports/${id}/escalate`), onSuccess: () => { refresh(); toast.success("Incident returned to the fallback matching queue"); } });
  const teamName = (id: string) => teams.data?.find((team) => team.id === id)?.name ?? id;
  const toggleTeam = (id: string) => setSelectedTeams((current) => current.includes(id) ? current.filter((teamId) => teamId !== id) : [...current, id]);

  return <section className="mb-5" data-testid="live-dispatch-board">
    <Card className="border-slate-200 bg-white py-0 shadow-sm">
      <CardHeader className="border-b border-slate-100 px-5 py-4">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div><CardTitle className="flex items-center gap-2 text-lg"><Activity className="size-4 text-[#8b0000]" /> Real-time civilian dispatch queue</CardTitle><p className="mt-1 text-xs text-slate-500">Event-driven reports · capability, distance and workload matching · fallback escalation.</p></div>
          <div className="flex items-center gap-3"><span className={`flex items-center gap-2 font-mono text-[9px] uppercase tracking-wider ${eventsConnected ? "text-green-700" : "text-amber-700"}`}><span className={`size-1.5 animate-pulse rounded-full ${eventsConnected ? "bg-green-500" : "bg-amber-500"}`} />{eventsConnected ? "Event stream live" : "Polling fallback"}</span><Badge data-testid="dispatch-open-count" className="bg-[#1e293b] text-white">{sortedReports.filter((report) => report.status !== "RESOLVED").length} open</Badge></div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-0 p-0 lg:grid-cols-[0.86fr_1.14fr]">
        <div className="max-h-[560px] overflow-y-auto border-b border-slate-100 p-3 lg:border-b-0 lg:border-r">
          {sortedReports.length ? <div className="space-y-2">{sortedReports.map((report) => <button type="button" key={report.id} data-testid={`dispatch-report-${report.id}`} onClick={() => setSelected(report)} className={`w-full rounded-xl border p-3 text-left ${selected?.id === report.id ? "border-red-300 bg-red-50" : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"}`}><div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="truncate text-sm font-bold text-slate-900">{report.title}</p><p className="mt-1 flex items-center gap-1 text-[10px] text-slate-500"><MapPin className="size-3" /> {report.location_name}</p></div><Badge variant="outline" className={`shrink-0 text-[8px] ${statusTone[report.status]}`}>{report.status.replaceAll("_", " ")}</Badge></div><div className="mt-3 flex items-center justify-between"><span className="text-[9px] text-slate-400">{report.reporter_name} · {report.severity}</span><ChevronRight className="size-3.5 text-slate-400" /></div></button>)}</div> : <div className="py-14 text-center" data-testid="dispatch-empty"><ShieldCheck className="mx-auto size-7 text-green-500" /><p className="mt-3 text-sm font-bold text-slate-800">Queue clear</p><p className="mt-1 text-xs text-slate-500">New civilian reports will appear here instantly.</p></div>}
        </div>
        <div className="min-h-[390px] max-h-[760px] overflow-y-auto p-4">
          {selected ? <div data-testid="dispatch-selected-report">
            <div className="flex items-start justify-between gap-4"><div><div className="flex items-center gap-2"><Badge variant="outline" className={`text-[8px] ${statusTone[selected.status]}`}>{selected.status.replaceAll("_", " ")}</Badge><span className="font-mono text-[9px] text-slate-400">{selected.id.slice(0, 8).toUpperCase()}</span></div><h3 className="mt-2 text-xl font-bold text-slate-950">{selected.title}</h3><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{selected.description}</p></div><Button type="button" aria-label="Close dispatch detail" data-testid="dispatch-close-button" variant="ghost" size="icon-sm" onClick={() => setSelected(null)}><X className="size-4" /></Button></div>
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">{[["Category", selected.category], ["Severity", selected.severity], ["Location", selected.location_name], ["Reporter", selected.reporter_name]].map(([label, value]) => <div key={label} className="rounded-lg bg-slate-50 p-3"><p className="font-mono text-[8px] uppercase text-slate-400">{label}</p><p className="mt-1 truncate text-xs font-semibold text-slate-800">{value}</p></div>)}</div>
            {selected.status === "NEW" && <Button type="button" data-testid="dispatch-acknowledge-button" onClick={() => acknowledge.mutate(selected.id)} disabled={acknowledge.isPending} className="mt-4 bg-amber-500 font-bold text-slate-950 hover:bg-amber-400"><Check className="size-4" /> Acknowledge report</Button>}
            {selected.status !== "RESOLVED" && <div className="mt-5 border-t border-slate-100 pt-4"><div className="flex items-center justify-between"><div><p className="flex items-center gap-2 text-sm font-bold text-slate-900"><Sparkles className="size-4 text-amber-600" /> Hero recommendations</p><p className="mt-1 text-[10px] text-slate-500">Score = capability + proximity + availability + workload</p></div><Users className="size-4 text-slate-400" /></div><div className="mt-3 grid gap-2 sm:grid-cols-2">{recommendations.data?.map((recommendation, index) => <div key={recommendation.team.id} data-testid={`dispatch-team-${recommendation.team.id}`} className={`rounded-xl border p-3 ${selectedTeams.includes(recommendation.team.id) ? "border-red-300 bg-red-50/60" : "border-slate-200"}`}><div className="flex items-start justify-between gap-3"><label className="flex cursor-pointer items-start gap-2"><input type="checkbox" data-testid={`dispatch-team-checkbox-${recommendation.team.id}`} checked={selectedTeams.includes(recommendation.team.id)} onChange={() => toggleTeam(recommendation.team.id)} className="mt-0.5 accent-[#8b0000]" /><span><span className="block text-xs font-bold text-slate-900">{recommendation.team.name}</span><span className="mt-1 block text-[9px] text-slate-500">{recommendation.distance_km} km · {recommendation.team.status} · {recommendation.team.active_incidents} active</span></span></label><span className={`font-mono text-sm font-bold ${index === 0 ? "text-green-700" : "text-slate-600"}`}>{recommendation.score}</span></div><div className="mt-2 flex items-center justify-between"><span className={`text-[8px] font-bold uppercase ${recommendation.capability_match ? "text-green-700" : "text-amber-700"}`}>{recommendation.capability_match ? "Capability match" : "Support team"}</span><label className="flex cursor-pointer items-center gap-1 text-[8px] font-bold uppercase text-slate-500"><input type="radio" name="primary-team" data-testid={`dispatch-primary-${recommendation.team.id}`} checked={primaryTeam === recommendation.team.id} onChange={() => { setPrimaryTeam(recommendation.team.id); if (!selectedTeams.includes(recommendation.team.id)) setSelectedTeams((current) => [...current, recommendation.team.id]); }} className="accent-[#8b0000]" /> Primary</label></div></div>)}</div><Button type="button" data-testid="dispatch-assign-button" disabled={!selectedTeams.length || !primaryTeam || assign.isPending} onClick={() => assign.mutate({ id: selected.id, teamIds: selectedTeams, primary: primaryTeam })} className="mt-3 w-full bg-[#8b0000] font-bold text-white hover:bg-[#a30d1b]"><Route className="size-4" /> {assign.isPending ? "Dispatching…" : "Assign selected hero teams"}</Button></div>}
            {selected.assigned_team_ids.length > 0 && <div className="mt-4 rounded-xl border border-orange-200 bg-orange-50 p-3" data-testid="dispatch-assigned-teams"><p className="font-mono text-[8px] font-bold uppercase text-orange-700">Assigned response</p><p className="mt-1 text-xs text-orange-950">{selected.assigned_team_ids.map(teamName).join(" · ")}</p></div>}
            {selected.status === "TEAM_ASSIGNED" && <Button type="button" data-testid="dispatch-escalate-button" variant="outline" className="mt-3 border-red-200 text-red-700 hover:bg-red-50" onClick={() => escalate.mutate(selected.id)}><AlertTriangle className="size-4" /> Escalate / rematch unresponsive team</Button>}
            <div className="mt-5 border-t border-slate-100 pt-4"><p className="flex items-center gap-2 text-xs font-bold text-slate-800"><Clock3 className="size-3.5" /> Response timeline</p><div className="mt-3 space-y-2">{selected.timeline.slice().reverse().map((event, index) => <div key={`${event.timestamp}-${index}`} className="flex gap-2 text-[10px]"><span className="mt-1 size-2 shrink-0 rounded-full bg-[#8b0000]" /><span><strong className="text-slate-700">{event.status.replaceAll("_", " ")}</strong><span className="text-slate-500"> — {event.note} · {event.actor_name}</span></span></div>)}</div></div>
            <div className="mt-4"><IncidentComms reportId={selected.id} /></div>
          </div> : <div className="grid h-full min-h-80 place-items-center text-center" data-testid="dispatch-select-prompt"><div><Radio className="mx-auto size-8 text-slate-300" /><p className="mt-3 text-sm font-bold text-slate-700">Select an incident to coordinate</p><p className="mt-1 max-w-sm text-xs leading-5 text-slate-500">The dispatch engine will rank every available hero and explain why.</p></div></div>}
        </div>
      </CardContent>
    </Card>
  </section>;
}