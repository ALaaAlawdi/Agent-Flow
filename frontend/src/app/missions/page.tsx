"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { api, CompanyEvent, MissionDetail, MissionPacket, MissionSummary, MissionTask } from "@/lib/api";
import { BriefcaseBusiness, CheckCircle2, Clock3, ShieldAlert, Zap } from "lucide-react";

const RISK_STYLES: Record<MissionSummary["risk"], string> = {
  low: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
  medium: "bg-amber-500/10 text-amber-300 border-amber-500/20",
  high: "bg-orange-500/10 text-orange-300 border-orange-500/20",
  critical: "bg-rose-500/10 text-rose-300 border-rose-500/20",
};

const STATUS_STYLES: Record<MissionTask["status"], string> = {
  blocked: "border-zinc-800 bg-zinc-900/60",
  ready: "border-violet-500/30 bg-violet-500/5",
  done: "border-emerald-500/30 bg-emerald-500/5",
};

const STATUS_LABELS: Array<{ key: MissionTask["status"]; label: string }> = [
  { key: "blocked", label: "Blocked" },
  { key: "ready", label: "Ready" },
  { key: "done", label: "Done" },
];

const INITIAL_FORM = {
  title: "",
  brief: "",
  budget: 120,
  risk: "medium" as MissionSummary["risk"],
};

export default function MissionsPage() {
  const [missions, setMissions] = useState<MissionSummary[]>([]);
  const [selectedMissionId, setSelectedMissionId] = useState("");
  const [selectedMission, setSelectedMission] = useState<MissionDetail | null>(null);
  const [events, setEvents] = useState<CompanyEvent[]>([]);
  const [packets, setPackets] = useState<MissionPacket[]>([]);
  const [form, setForm] = useState(INITIAL_FORM);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formingSquad, setFormingSquad] = useState(false);
  const [error, setError] = useState("");

  const groupedTasks = useMemo(() => {
    if (!selectedMission) return { blocked: [], ready: [], done: [] } satisfies Record<MissionTask["status"], MissionTask[]>;
    return {
      blocked: selectedMission.tasks.filter((task) => task.status === "blocked"),
      ready: selectedMission.tasks.filter((task) => task.status === "ready"),
      done: selectedMission.tasks.filter((task) => task.status === "done"),
    } satisfies Record<MissionTask["status"], MissionTask[]>;
  }, [selectedMission]);

  const loadMissions = async (preferredMissionId?: string) => {
    const missionResponse = await api.listMissions();
    const nextMissions = missionResponse.missions;
    setMissions(nextMissions);

    const nextSelectedId = preferredMissionId ?? selectedMissionId ?? nextMissions[0]?.id ?? "";
    setSelectedMissionId(nextSelectedId);

    if (nextSelectedId) {
      const [missionDetail, eventResponse] = await Promise.all([
        api.getMission(nextSelectedId),
        api.getCompanyEvents(),
      ]);
      setSelectedMission(missionDetail);
      setEvents(eventResponse.events.slice(-12).reverse());
      try {
        const packetResponse = await api.getMissionPackets(nextSelectedId);
        setPackets(packetResponse.packets);
      } catch {
        setPackets([]);
      }
    } else {
      const eventResponse = await api.getCompanyEvents();
      setSelectedMission(null);
      setEvents(eventResponse.events.slice(-12).reverse());
      setPackets([]);
    }
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        await loadMissions();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load missions");
      } finally {
        setLoading(false);
      }
    };
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectMission = async (missionId: string) => {
    setSelectedMissionId(missionId);
    setLoading(true);
    setError("");
    try {
      await loadMissions(missionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load mission");
    } finally {
      setLoading(false);
    }
  };

  const submitMission = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const created = await api.createMission(form);
      setForm(INITIAL_FORM);
      await loadMissions(created.mission_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create mission");
    } finally {
      setSubmitting(false);
    }
  };

  const formSquad = async () => {
    if (!selectedMissionId) return;
    setFormingSquad(true);
    setError("");
    try {
      await api.formMissionSquad(selectedMissionId);
      await loadMissions(selectedMissionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to form squad");
    } finally {
      setFormingSquad(false);
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <BriefcaseBusiness className="w-8 h-8 text-violet-400" />
            Missions Control Room
          </h1>
          <p className="text-zinc-400 text-sm mt-2 max-w-3xl">
            Turn Agent-Flow into a visible operating company: create venture missions, form squads, inspect ready work packets, and watch the event ledger update in real time.
          </p>
        </div>
        <Link
          href="/world"
          className="inline-flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/60 px-4 py-2 text-sm text-zinc-300 hover:text-white hover:border-violet-500/30"
        >
          <Zap className="w-4 h-4" />
          Back to AgentVerse
        </Link>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[360px_minmax(0,1fr)] gap-6">
        <section className="space-y-6">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-4 h-4 text-violet-400" />
              <h2 className="text-white font-semibold">Create mission</h2>
            </div>
            <form className="space-y-3" onSubmit={submitMission}>
              <input
                value={form.title}
                onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
                placeholder="Mission title"
                className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500/40"
              />
              <textarea
                value={form.brief}
                onChange={(e) => setForm((prev) => ({ ...prev, brief: e.target.value }))}
                placeholder="What expensive customer pain or product thesis are we validating?"
                rows={4}
                className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500/40"
              />
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="number"
                  min={1}
                  value={form.budget}
                  onChange={(e) => setForm((prev) => ({ ...prev, budget: Number(e.target.value) || 1 }))}
                  className="rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white focus:outline-none focus:border-violet-500/40"
                />
                <select
                  value={form.risk}
                  onChange={(e) => setForm((prev) => ({ ...prev, risk: e.target.value as MissionSummary["risk"] }))}
                  className="rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white focus:outline-none focus:border-violet-500/40"
                >
                  <option value="low">Low risk</option>
                  <option value="medium">Medium risk</option>
                  <option value="high">High risk</option>
                  <option value="critical">Critical risk</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-xl bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-3 text-sm font-medium text-white transition-opacity disabled:opacity-50"
              >
                {submitting ? "Creating mission..." : "Create mission"}
              </button>
            </form>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white font-semibold">Mission queue</h2>
              <span className="text-xs text-zinc-500">{missions.length} total</span>
            </div>

            <div className="space-y-3 max-h-[620px] overflow-y-auto pr-1">
              {missions.map((mission) => {
                const selected = mission.id === selectedMissionId;
                return (
                  <button
                    key={mission.id}
                    onClick={() => void selectMission(mission.id)}
                    className={`w-full text-left rounded-2xl border p-4 transition-all ${selected ? "border-violet-500/40 bg-violet-500/10" : "border-zinc-800 bg-zinc-950/80 hover:border-zinc-700"}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-sm font-medium text-white">{mission.title}</h3>
                        <p className="text-xs text-zinc-500 mt-1 line-clamp-2">{mission.brief}</p>
                      </div>
                      <span className={`rounded-full border px-2.5 py-1 text-[11px] capitalize ${RISK_STYLES[mission.risk]}`}>
                        {mission.risk}
                      </span>
                    </div>
                    <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
                      <div className="rounded-xl bg-zinc-900/70 p-2 text-zinc-300">
                        <div className="text-violet-300 font-semibold">{mission.task_counts.ready}</div>
                        <div className="text-zinc-500">Ready</div>
                      </div>
                      <div className="rounded-xl bg-zinc-900/70 p-2 text-zinc-300">
                        <div className="text-amber-300 font-semibold">{mission.task_counts.blocked}</div>
                        <div className="text-zinc-500">Blocked</div>
                      </div>
                      <div className="rounded-xl bg-zinc-900/70 p-2 text-zinc-300">
                        <div className="text-emerald-300 font-semibold">{mission.task_counts.done}</div>
                        <div className="text-zinc-500">Done</div>
                      </div>
                    </div>
                  </button>
                );
              })}

              {!missions.length && !loading && (
                <div className="rounded-2xl border border-dashed border-zinc-800 p-8 text-center text-sm text-zinc-500">
                  No missions yet. Create the first live company objective.
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="space-y-6">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5">
            {selectedMission ? (
              <>
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`rounded-full border px-2.5 py-1 text-[11px] capitalize ${RISK_STYLES[selectedMission.risk]}`}>
                        {selectedMission.risk}
                      </span>
                      <span className="rounded-full border border-zinc-700 px-2.5 py-1 text-[11px] capitalize text-zinc-300">
                        {selectedMission.status}
                      </span>
                    </div>
                    <h2 className="text-2xl font-semibold text-white">{selectedMission.title}</h2>
                    <p className="mt-2 max-w-3xl text-sm text-zinc-400">{selectedMission.brief}</p>
                  </div>
                  <button
                    onClick={() => void formSquad()}
                    disabled={formingSquad}
                    className="rounded-xl border border-violet-500/30 bg-violet-500/10 px-4 py-2.5 text-sm font-medium text-violet-200 hover:bg-violet-500/20 disabled:opacity-50"
                  >
                    {formingSquad ? "Forming squad..." : "Form squad"}
                  </button>
                </div>

                <div className="mt-5 grid grid-cols-2 lg:grid-cols-4 gap-3">
                  <MetricCard label="Budget used" value={`${selectedMission.budget_spent}/${selectedMission.budget_total}`} icon={<ShieldAlert className="w-4 h-4 text-amber-300" />} />
                  <MetricCard label="Ready tasks" value={String(selectedMission.tasks.filter((task) => task.status === "ready").length)} icon={<Clock3 className="w-4 h-4 text-violet-300" />} />
                  <MetricCard label="Completed" value={String(selectedMission.tasks.filter((task) => task.status === "done").length)} icon={<CheckCircle2 className="w-4 h-4 text-emerald-300" />} />
                  <MetricCard label="Workers assigned" value={String(new Set(selectedMission.tasks.map((task) => task.assigned_agent).filter(Boolean)).size)} icon={<BriefcaseBusiness className="w-4 h-4 text-cyan-300" />} />
                </div>
              </>
            ) : (
              <div className="py-10 text-center text-zinc-500">Select or create a mission to inspect its board.</div>
            )}
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] gap-6">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-white font-semibold">Task board</h2>
                <span className="text-xs text-zinc-500">Deterministic company workflow</span>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {STATUS_LABELS.map(({ key, label }) => (
                  <div key={key} className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-3">
                    <div className="mb-3 flex items-center justify-between">
                      <h3 className="text-sm font-medium text-white">{label}</h3>
                      <span className="rounded-full bg-zinc-900 px-2 py-0.5 text-[11px] text-zinc-500">
                        {groupedTasks[key].length}
                      </span>
                    </div>
                    <div className="space-y-3">
                      {groupedTasks[key].map((task) => (
                        <article key={task.id} className={`rounded-2xl border p-3 ${STATUS_STYLES[task.status]}`}>
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <h4 className="text-sm font-medium text-white">{task.title}</h4>
                              <p className="mt-1 text-xs uppercase tracking-wide text-zinc-500">{task.capability}</p>
                            </div>
                            <span className="rounded-full bg-zinc-900 px-2 py-1 text-[11px] text-zinc-400">
                              {task.cost} cr
                            </span>
                          </div>
                          <div className="mt-3 space-y-2 text-xs text-zinc-400">
                            <div>Assigned: <span className="text-zinc-200">{task.assigned_agent || "Unassigned"}</span></div>
                            <div>Depends on: <span className="text-zinc-200">{task.depends_on.length ? task.depends_on.join(", ") : "None"}</span></div>
                            {task.evidence && (
                              <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-2 text-zinc-300">
                                <div className="font-medium text-white mb-1">Evidence</div>
                                <div className="line-clamp-2">{task.evidence.summary}</div>
                              </div>
                            )}
                          </div>
                        </article>
                      ))}
                      {!groupedTasks[key].length && (
                        <div className="rounded-2xl border border-dashed border-zinc-800 p-4 text-center text-xs text-zinc-600">
                          No {label.toLowerCase()} tasks.
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-6">
              <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-white font-semibold">Ready worker packets</h2>
                  <span className="text-xs text-zinc-500">{packets.length}</span>
                </div>
                <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
                  {packets.map((packet) => (
                    <div key={packet.task_id} className="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-3">
                      <div className="text-sm font-medium text-white">{packet.objective}</div>
                      <div className="mt-1 text-xs text-zinc-400">Worker: <span className="text-zinc-200">{packet.worker_id}</span></div>
                      <div className="mt-1 text-xs text-zinc-400">Evidence contract: <span className="text-zinc-200">{packet.evidence_contract.join(", ")}</span></div>
                    </div>
                  ))}
                  {!packets.length && (
                    <div className="rounded-2xl border border-dashed border-zinc-800 p-4 text-center text-xs text-zinc-600">
                      Form a squad to emit ready task packets.
                    </div>
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-white font-semibold">Event ledger</h2>
                  <span className="text-xs text-zinc-500">latest 12</span>
                </div>
                <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
                  {events.map((event) => (
                    <div key={event.id} className="rounded-2xl border border-zinc-800 bg-zinc-950/80 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm font-medium text-white">{event.type}</span>
                        <span className="text-[11px] text-zinc-500">{new Date(event.occurred_at).toLocaleString()}</span>
                      </div>
                      <div className="mt-1 text-xs text-zinc-400">Actor: <span className="text-zinc-200">{event.actor}</span></div>
                      <pre className="mt-2 whitespace-pre-wrap break-words rounded-xl bg-zinc-900/80 p-2 text-[11px] text-zinc-500">{JSON.stringify(event.payload, null, 2)}</pre>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function MetricCard({ label, value, icon }: { label: string; value: string; icon: ReactNode }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/80 p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-xs text-zinc-500">{label}</div>
          <div className="mt-1 text-lg font-semibold text-white">{value}</div>
        </div>
        <div>{icon}</div>
      </div>
    </div>
  );
}
