"use client";

export type WorldPulseStatus = "idle" | "running" | "paused" | "crashed";

export type WorldPulseProps = {
  tick: number;
  status: WorldPulseStatus;
  paceSeconds: number;
  uptimeSeconds: number;
  agentCount: number;
  totalInteractions: number;
  totalLearnings: number;
};

const DOT_COLOR: Record<WorldPulseStatus, string> = {
  idle:    "bg-amber-400",
  running: "bg-emerald-400 animate-pulse",
  paused:  "bg-zinc-500",
  crashed: "bg-rose-500",
};

const STATUS_LABEL: Record<WorldPulseStatus, string> = {
  idle:    "idle",
  running: "running",
  paused:  "paused",
  crashed: "crashed",
};

function formatUptime(sec: number): string {
  if (sec < 60) return `${sec.toFixed(0)}s`;
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}m ${s}s`;
}

export default function WorldPulse({
  tick, status, paceSeconds, uptimeSeconds, agentCount, totalInteractions, totalLearnings,
}: WorldPulseProps) {
  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-zinc-900/60 border border-zinc-800 rounded-xl text-xs tabular-nums text-zinc-300">
      <span className="flex items-center gap-1.5">
        <span className={`inline-block h-2 w-2 rounded-full ${DOT_COLOR[status]}`} />
        <span className="capitalize">{STATUS_LABEL[status]}</span>
      </span>
      <span className="text-zinc-600">·</span>
      <span>tick <span className="text-white">{tick}</span></span>
      <span className="text-zinc-600">·</span>
      <span>pace <span className="text-white">{paceSeconds.toFixed(1)}s</span></span>
      <span className="text-zinc-600">·</span>
      <span>{agentCount} agents</span>
      <span className="text-zinc-600">·</span>
      <span>↔ {totalInteractions}</span>
      <span className="text-zinc-600">·</span>
      <span>✨ {totalLearnings}</span>
      <span className="ml-auto text-zinc-500">{formatUptime(uptimeSeconds)}</span>
    </div>
  );
}
