"use client";

export type BrainSnapshot = {
  role: string;
  personality: { curiosity: number; talkativity: number; friendliness: number };
  skills: Array<{ name: string; confidence: number; times_used: number }>;
  memory_count: number;
  knowledge_recent: string[];
  questions_asked: number;
  questions_answered: number;
};

export type AgentLearningCardsProps = {
  agents: Array<{ agent_id: string; name: string }>;
  brains: Record<string, BrainSnapshot>;
  recentDeltas: Record<string, { asked?: boolean; answered?: boolean; memories?: boolean; skills?: boolean }>;
  agentColors: Record<string, string>;
};

function Bar({ value, label, color = "bg-violet-500" }: { value: number; label: string; color?: string }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className="flex items-center gap-1.5 text-[10px]">
      <span className="w-14 text-zinc-500">{label}</span>
      <div className="flex-1 h-1 bg-zinc-800 rounded overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-6 text-right text-zinc-400 tabular-nums">{Math.round(pct)}%</span>
    </div>
  );
}

function Counter({ label, value, flash, icon }: { label: string; value: number; flash?: boolean; icon: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 tabular-nums ${flash ? "lv-flash" : ""}`}>
      <span aria-hidden>{icon}</span>
      <span className="text-zinc-500">{label}</span>
      <span className="text-white">{value}</span>
    </span>
  );
}

export default function AgentLearningCards({
  agents, brains, recentDeltas, agentColors,
}: AgentLearningCardsProps) {
  if (agents.length === 0) {
    return <p className="text-zinc-600 text-xs">No agents yet.</p>;
  }
  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-2">
      {agents.map((a) => {
        const brain = brains[a.agent_id];
        const color = agentColors[a.agent_id] ?? "#8b5cf6";
        const delta = recentDeltas[a.agent_id] ?? {};
        if (!brain) {
          return (
            <div key={a.agent_id} className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-3">
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-white text-sm font-medium">{a.name}</span>
                <span className="text-zinc-500 text-xs">loading…</span>
              </div>
            </div>
          );
        }
        return (
          <div key={a.agent_id} className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-white text-sm font-medium">{a.name}</span>
              <span className="text-zinc-500 text-[10px] uppercase tracking-wider">{brain.role}</span>
            </div>

            <div className="space-y-1 mb-2">
              <Bar label="curiosity"    value={brain.personality.curiosity}    color="bg-amber-400" />
              <Bar label="talkativity"  value={brain.personality.talkativity}  color="bg-sky-400" />
              <Bar label="friendliness" value={brain.personality.friendliness} color="bg-emerald-400" />
            </div>

            <div className="space-y-1 mb-2">
              {brain.skills.slice(0, 3).map((s) => (
                <div key={s.name} className={`flex items-center gap-1.5 text-[10px] ${delta.skills ? "lv-flash rounded" : ""}`}>
                  <span className="w-14 text-zinc-400 truncate">{s.name}</span>
                  <div className="flex-1 h-1 bg-zinc-800 rounded overflow-hidden">
                    <div className="h-full bg-violet-500" style={{ width: `${s.confidence * 100}%` }} />
                  </div>
                  <span className="w-8 text-right text-zinc-500 tabular-nums">×{s.times_used}</span>
                </div>
              ))}
            </div>

            <div className="flex flex-wrap gap-1 text-[10px] mb-1">
              <Counter label="asked"    value={brain.questions_asked}    flash={delta.asked}    icon="🙋" />
              <Counter label="answered" value={brain.questions_answered} flash={delta.answered} icon="💬" />
              <Counter label="memories" value={brain.memory_count}       flash={delta.memories} icon="🤝" />
            </div>

            {brain.knowledge_recent.length > 0 && (
              <div className="text-[10px] text-zinc-500 mt-1 truncate">
                📖 {brain.knowledge_recent.slice(-3).join(" · ")}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
