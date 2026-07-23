"use client";

import { useEffect, useState } from "react";

export default function JobHunterPage() {
  const [data, setData] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  const load = async () => {
    const res = await fetch("/api/jobs/dashboard");
    setData(await res.json());
  };

  useEffect(() => { load(); }, []);

  const autoApply = async () => {
    setLoading(true);
    const res = await fetch("/api/jobs/auto-apply", { method: "POST" });
    const d = await res.json();
    setResults(d.results || []);
    setLoading(false);
    load();
  };

  const matchJob = async (jobId: string) => {
    const res = await fetch(`/api/jobs/match/${jobId}`, { method: "POST" });
    return await res.json();
  };

  const jobs = data.jobs || [];
  const apps = data.applications || [];
  const profile = data.profile || {};

  return (
    <div className="p-6 max-w-5xl mx-auto" dir="ltr">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">💼 Job Hunter</h1>
          <p className="text-zinc-500 text-sm mt-1">Hermes Agents — automated job applications</p>
        </div>
        <button
          onClick={autoApply}
          disabled={loading}
          className="px-6 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:from-zinc-700 text-white rounded-xl font-semibold text-sm"
        >
          {loading ? "⏳ Applying..." : "🚀 Auto-Apply All"}
        </button>
      </div>

      {/* Profile */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-5 mb-6">
        <h2 className="text-sm font-semibold text-white mb-3">👤 Profile</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div><span className="text-zinc-500">Name:</span> <span className="text-white">{profile.name}</span></div>
          <div><span className="text-zinc-500">Email:</span> <span className="text-white">{profile.email}</span></div>
          <div><span className="text-zinc-500">Title:</span> <span className="text-white">{profile.title}</span></div>
          <div><span className="text-zinc-500">Location:</span> <span className="text-white">{profile.location}</span></div>
        </div>
        <div className="flex gap-1 mt-3 flex-wrap">
          {(profile.skills || []).slice(0, 8).map((s:string) => (
            <span key={s} className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 text-xs">{s}</span>
          ))}
        </div>
      </div>

      {/* Job Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {jobs.map((job: any) => (
          <div key={job.id} className={`bg-zinc-900/50 border rounded-2xl p-5 ${job.applied ? "border-emerald-500/30" : "border-zinc-800"}`}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-white font-semibold text-sm">{job.title}</h3>
                <p className="text-zinc-400 text-xs">{job.company}</p>
              </div>
              {job.applied ? (
                <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs rounded">Applied ✅</span>
              ) : (
                <span className="px-2 py-0.5 bg-zinc-800 text-zinc-500 text-xs rounded">Ready</span>
              )}
            </div>
            <div className="space-y-1 text-xs text-zinc-500 mb-3">
              <p>📍 {job.location}</p>
              <p>💰 {job.salary || "Competitive"}</p>
              <p>📅 {job.posted}</p>
            </div>
            <button
              onClick={() => matchJob(job.id).then(m => alert(`Match: ${m.match_score}% — ${m.recommendation}\n\n${m.reason}`))}
              className="w-full py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-xs transition-colors"
            >
              🎯 Analyze Match
            </button>
          </div>
        ))}
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="bg-emerald-900/20 border border-emerald-500/30 rounded-2xl p-5 mb-6">
          <h2 className="text-emerald-400 font-semibold text-sm mb-3">✅ Auto-Apply Results</h2>
          {results.map((r: any, i: number) => (
            <div key={i} className="flex items-center justify-between py-1.5 border-b border-emerald-500/10 last:border-0">
              <span className="text-white text-sm">{r.company} — {r.title}</span>
              <span className="text-emerald-400 text-xs">Match: {r.match_score}%</span>
            </div>
          ))}
        </div>
      )}

      {/* Applications */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-5">
        <h2 className="text-sm font-semibold text-white mb-3">📊 Applications ({apps.length})</h2>
        {apps.length === 0 ? (
          <p className="text-zinc-600 text-sm text-center py-4">No applications yet. Click Auto-Apply.</p>
        ) : (
          <div className="space-y-2">
            {apps.map((app: any) => (
              <div key={app.id} className="flex items-center justify-between bg-zinc-800/30 rounded-lg p-3">
                <div>
                  <p className="text-white text-sm">{app.title} <span className="text-zinc-500">at</span> {app.company}</p>
                  <p className="text-zinc-600 text-xs">Applied: {app.applied_at}</p>
                </div>
                <span className={`px-2 py-0.5 rounded text-xs ${
                  app.status === "applied" ? "bg-blue-500/20 text-blue-400" :
                  app.status === "interview" ? "bg-yellow-500/20 text-yellow-400" :
                  app.status === "offered" ? "bg-emerald-500/20 text-emerald-400" :
                  "bg-red-500/20 text-red-400"
                }`}>{app.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}