import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { ArrowRight, Building2, Eye, EyeOff, LockKeyhole, ShieldCheck, Siren, UserRound, UsersRound } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Toaster } from "@/components/ui/sonner";
import { apiPost, ApiError } from "@/lib/api";
import { beginSession } from "@/lib/session";
import { queryClient } from "@/lib/queryClient";
import { routeForRole } from "@/pages/RoleLanding";
import type { UserPublic, UserRole } from "@/lib/types";

const portals: Array<{ role: UserRole; label: string; note: string; icon: typeof UserRound }> = [
  { role: "CIVILIAN", label: "Civilian / Student", note: "Report and track an issue", icon: UserRound },
  { role: "OFFICER", label: "Control Room", note: "Validate and dispatch heroes", icon: ShieldCheck },
  { role: "RESPONSE_TEAM", label: "Response Team", note: "Receive and resolve missions", icon: Siren },
];

function errorMessage(error: unknown) {
  if (error instanceof ApiError && typeof error.body === "object" && error.body !== null && "detail" in error.body) return String((error.body as { detail: unknown }).detail);
  return "We could not complete that request. Check your details and try again.";
}

export default function Auth() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [portal, setPortal] = useState<UserRole>("CIVILIAN");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const authMutation = useMutation({
    mutationFn: async (payload: { full_name?: string; email: string; password: string; portal_role?: UserRole }) => {
      // Vercel is currently hosting the frontend without the FastAPI service.
      // Keep the real API path for development, but use a browser-only demo
      // session in production so the existing UI and dashboards remain unchanged.
      if (false) {
        return apiPost<UserPublic>(`/auth/${mode}`, payload);
      }

      const emailAddress = payload.email.trim().toLowerCase();
      const savedUsers = JSON.parse(localStorage.getItem("kiit-demo-users") || "{}");

      if (mode === "signup") {
        const user: UserPublic = {
          id: `demo-${Date.now()}`,
          full_name: payload.full_name?.trim() || "KIIT Student",
          email: emailAddress,
          role: "CIVILIAN",
          created_at: new Date().toISOString(),
        };
        savedUsers[emailAddress] = { ...user, password: payload.password };
        localStorage.setItem("kiit-demo-users", JSON.stringify(savedUsers));
        localStorage.setItem("kiit-demo-user", JSON.stringify(user));
        return user;
      }

      if (!emailAddress || !payload.password) {
        throw new Error("Please enter your email and password.");
      }

      const seeded: Record<string, UserPublic & { password: string }> = {
        "student@demo.com": { id: "demo-student", full_name: "Demo Student", email: emailAddress, role: "CIVILIAN", created_at: "2026-09-27T00:00:00.000Z", password: "Demo123!" },
        "control@demo.com": { id: "demo-control", full_name: "Control Room Officer", email: emailAddress, role: "OFFICER", created_at: "2026-09-27T00:00:00.000Z", password: "Demo123!" },
        "responder@demo.com": { id: "demo-responder", full_name: "Response Team Alpha", email: emailAddress, role: "RESPONSE_TEAM", created_at: "2026-09-27T00:00:00.000Z", password: "Demo123!" },
      };

      const user = seeded[emailAddress] || savedUsers[emailAddress];

      if (!user) {
        throw new Error("Demo account not found. Use the demo credentials shown above or create a civilian account.");
      }

      if (user.role !== (payload.portal_role || "CIVILIAN")) {
        throw new Error("Please use the account for the selected portal.");
      }

      if (user.password !== payload.password) {
        throw new Error("Incorrect password. Please check your credentials and try again.");
      }

      const publicUser: UserPublic = {
        id: user.id,
        full_name: user.full_name,
        email: user.email,
        role: user.role,
        created_at: user.created_at,
      };
      localStorage.setItem("kiit-demo-user", JSON.stringify(publicUser));
      return publicUser;
    },
    onSuccess: (user) => {
      beginSession();
      queryClient.setQueryData(["auth", "me"], user);
      toast.success(mode === "login" ? `Welcome, ${user.full_name.split(" ")[0]}` : "Civilian account created");
      navigate(routeForRole(user.role));
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : errorMessage(error)),
  });
  const switchMode = (next: "login" | "signup") => { setMode(next); if (next === "signup") setPortal("CIVILIAN"); };
  const submit = (event: FormEvent) => { event.preventDefault(); authMutation.mutate(mode === "signup" ? { full_name: fullName, email, password } : { email, password, portal_role: portal }); };
  const demoHint = mode === "signup" ? "Create your own civilian account" : portal === "CIVILIAN" ? "Demo: student@demo.com / Demo123!" : portal === "OFFICER" ? "Demo: control@demo.com / Demo123!" : "Demo: responder@demo.com / Demo123!";

  return <main className="min-h-svh bg-[#f6f3ef] text-slate-900" data-testid="auth-page"><div className="grid min-h-svh lg:grid-cols-[1.02fr_0.98fr]"><section className="relative hidden overflow-hidden bg-[#1e293b] p-10 text-white lg:flex lg:flex-col lg:justify-between xl:p-16" data-testid="auth-briefing-panel"><div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(30,41,59,.96),rgba(139,0,0,.58)),url('https://customer-assets-jai6qajn.emergentagent.net/job_kiit-incidents/artifacts/cbm36tib_KIIT-Campus-Front-Library-600x208.webp')] bg-cover bg-center" /><div className="relative z-10 flex items-center gap-3" data-testid="auth-brand-lockup"><div className="grid size-11 place-items-center rounded-lg border border-white/20 bg-[#8b0000]"><Building2 className="size-5 text-white" /></div><div><p className="font-heading text-xl font-extrabold">KIIT Safety Connect</p><p className="font-mono text-[9px] uppercase tracking-[0.22em] text-slate-300">Hero Dispatch Network</p></div></div><div className="relative z-10 max-w-2xl"><p className="font-mono text-[10px] uppercase tracking-[0.24em] text-amber-200">One core question</p><h1 className="mt-4 font-heading text-5xl font-extrabold leading-[1.02] tracking-tight xl:text-7xl" data-testid="auth-hero-heading">When something goes wrong,<br /><span className="text-amber-200">how does the right hero arrive fastest?</span></h1><p className="mt-6 max-w-xl text-base leading-7 text-slate-200">One connected flow from civilian report to control-room coordination and accountable field response—without letting a single issue fall through the cracks.</p><div className="mt-10 grid grid-cols-3 gap-3">{[{ icon: UserRound, label: "Report" }, { icon: ShieldCheck, label: "Coordinate" }, { icon: Siren, label: "Resolve" }].map((item, index) => <div key={item.label} className="rounded-xl border border-white/15 bg-black/20 p-4"><span className="font-mono text-[9px] text-amber-200">0{index + 1}</span><item.icon className="mt-6 size-4" /><p className="mt-2 text-xs font-bold">{item.label}</p></div>)}</div></div><div className="relative z-10 flex items-center gap-2 font-mono text-[9px] uppercase tracking-widest text-slate-300"><span className="size-1.5 animate-pulse rounded-full bg-green-400" /> KIIT campus response prototype online</div></section>
      <section className="flex items-center justify-center p-5 sm:p-10" data-testid="auth-form-panel"><div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_24px_70px_rgba(30,41,59,0.12)] sm:p-9"><div className="mb-7 flex items-center gap-3 lg:hidden"><div className="grid size-10 place-items-center rounded-lg bg-[#8b0000] text-white"><Building2 className="size-5" /></div><div><p className="font-heading font-extrabold">KIIT Safety Connect</p><p className="font-mono text-[8px] uppercase tracking-widest text-slate-500">Hero Dispatch Network</p></div></div><div className="flex items-start justify-between gap-4"><div><p className="font-mono text-[9px] font-bold uppercase tracking-[0.22em] text-[#8b0000]">Choose your portal</p><h2 className="mt-2 font-heading text-3xl font-extrabold tracking-tight text-slate-950" data-testid="auth-form-heading">{mode === "login" ? "Sign in to continue" : "Create civilian access"}</h2><p className="mt-2 text-sm text-slate-500">{mode === "login" ? "Each role opens a dashboard built for its next action." : "Officer and response-team access uses verified seeded accounts."}</p></div><UsersRound className="mt-1 size-6 text-slate-300" /></div>
        <div className="my-6 grid gap-2 sm:grid-cols-3" data-testid="auth-role-selector">{portals.map((item) => <button type="button" key={item.role} data-testid={`auth-role-${item.role.toLowerCase()}-button`} disabled={mode === "signup" && item.role !== "CIVILIAN"} onClick={() => setPortal(item.role)} className={`rounded-xl border p-3 text-left ${portal === item.role ? "border-red-300 bg-red-50 shadow-sm" : "border-slate-200 hover:border-slate-300"} disabled:cursor-not-allowed disabled:opacity-35`}><item.icon className={`size-4 ${portal === item.role ? "text-[#8b0000]" : "text-slate-400"}`} /><p className="mt-3 text-xs font-bold text-slate-900">{item.label}</p><p className="mt-1 text-[9px] leading-4 text-slate-500">{item.note}</p></button>)}</div>
        <div className="mb-5 grid grid-cols-2 rounded-xl bg-slate-100 p-1" data-testid="auth-mode-switcher"><button type="button" data-testid="auth-login-tab" onClick={() => switchMode("login")} className={`rounded-lg py-2.5 text-xs font-bold ${mode === "login" ? "bg-white text-[#8b0000] shadow-sm" : "text-slate-500"}`}>Sign in</button><button type="button" data-testid="auth-signup-tab" onClick={() => switchMode("signup")} className={`rounded-lg py-2.5 text-xs font-bold ${mode === "signup" ? "bg-white text-[#8b0000] shadow-sm" : "text-slate-500"}`}>Civilian sign up</button></div>
        {mode === "login" && <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 font-mono text-[9px] text-amber-900" data-testid="auth-demo-credentials">Demo access: {demoHint}</p>}
        <form onSubmit={submit} className="space-y-4" data-testid="auth-form">{mode === "signup" && <label className="block"><span className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-slate-600">Full name</span><div className="relative"><UserRound className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><Input required minLength={2} value={fullName} onChange={(event) => setFullName(event.target.value)} data-testid="auth-full-name-input" placeholder="Your name" className="h-11 pl-10" /></div></label>}<label className="block"><span className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-slate-600">Email</span><div className="relative"><UserRound className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><Input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} data-testid="auth-email-input" placeholder={portal === "CIVILIAN" ? "you@example.com" : "verified@kiit.ac.in"} className="h-11 pl-10" /></div></label><label className="block"><span className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-slate-600">Password</span><div className="relative"><LockKeyhole className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><Input required minLength={mode === "signup" ? 8 : 1} type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} data-testid="auth-password-input" placeholder="••••••••" className="h-11 pl-10 pr-11" /><button type="button" aria-label="Toggle password visibility" data-testid="auth-password-visibility-button" onClick={() => setShowPassword((value) => !value)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">{showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</button></div></label><Button type="submit" data-testid="auth-submit-button" disabled={authMutation.isPending} className="h-11 w-full bg-[#8b0000] font-bold text-white hover:bg-[#a30d1b]">{authMutation.isPending ? "Verifying…" : mode === "login" ? `Open ${portals.find((item) => item.role === portal)?.label} portal` : "Create civilian account"}<ArrowRight className="size-4" /></Button></form>
      </div></section></div><Toaster richColors /></main>;
}