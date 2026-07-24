"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import WorldPulse, { WorldPulseStatus } from "@/components/world/WorldPulse";
import InteractionStream, { InteractionEvent } from "@/components/world/InteractionStream";
import AgentLearningCards, { BrainSnapshot } from "@/components/world/AgentLearningCards";

type Agent = {
  agent_id: string;
  name: string;
  position: { x: number; y: number };
  state: string;
  energy: number;
  skills: string[];
  discovered: number;
  messages_sent: number;
  messages_received: number;
  brain?: BrainSnapshot;
};
type Location = { id: string; name: string; position: { x: number; y: number }; type: string };
type Message = { message_id: string; sender_name: string; content: string; target: string };
type Company = { name: string; description: string; position: { x: number; y: number }; employees: string[]; completed_tasks: number; revenue: number; status: string };
type WorldStats = {
  total_agents: number;
  uptime_seconds: number;
  total_interactions: number;
  total_learnings: number;
};
type WorldState = {
  name: string; width: number; height: number;
  agents: Agent[]; locations: Location[]; active_messages: Message[];
  companies?: Company[];
  stats?: WorldStats;
  tick?: number;
};

const AGENT_COLORS: Record<string, string> = {
  "agent-1": "#8b5cf6",
  "agent-2": "#06b6d4",
  "agent-3": "#f43f5e",
};
const COMPANY_COLORS: Record<string, string> = {
  "Agent-Flow": "#8b5cf6",
  "VirtualCorp": "#06b6d4",
  "Hermes Brain": "#f43f5e",
  "DataSphere": "#22c55e",
};

const WORLD_SIZE = 300;
const BG_COLOR = "#0f0f23";
const GRID_COLOR = "#1a1a3e";
const MAX_INTERACTIONS = 100;
const DELTA_FLASH_MS = 400;

export default function WorldPage() {
  const [state, setState] = useState<WorldState | null>(null);
  const [tick, setTick] = useState(0);
  const [tickerStatus, setTickerStatus] = useState<WorldPulseStatus>("idle");
  const [paceSeconds, setPaceSeconds] = useState(3);
  const [interactionEvents, setInteractionEvents] = useState<InteractionEvent[]>([]);
  const [brains, setBrains] = useState<Record<string, BrainSnapshot>>({});
  const [recentDeltas, setRecentDeltas] = useState<Record<string, { asked?: boolean; answered?: boolean; memories?: boolean; skills?: boolean }>>({});
  const [log, setLog] = useState<string[]>([]);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const flashTimersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const addLog = useCallback((msg: string) => {
    setLog((prev) => [...prev.slice(-49), `${new Date().toLocaleTimeString()} ${msg}`]);
  }, []);

  const appendInteraction = useCallback((ev: InteractionEvent) => {
    setInteractionEvents((prev) => {
      const next = [...prev, ev];
      return next.length > MAX_INTERACTIONS ? next.slice(-MAX_INTERACTIONS) : next;
    });
  }, []);

  const flashDelta = useCallback((agentId: string, keys: Array<"asked" | "answered" | "memories" | "skills">) => {
    setRecentDeltas((prev) => {
      const cur = prev[agentId] ?? {};
      const merged = { ...cur };
      for (const k of keys) merged[k] = true;
      return { ...prev, [agentId]: merged };
    });
    // Cancel any pending clear for this agent so a fresh event resets the 400ms window.
    const existing = flashTimersRef.current[agentId];
    if (existing) clearTimeout(existing);
    flashTimersRef.current[agentId] = setTimeout(() => {
      setRecentDeltas((prev) => {
        if (!prev[agentId]) return prev;
        const cleared = { ...prev };
        delete cleared[agentId];
        return cleared;
      });
      delete flashTimersRef.current[agentId];
    }, DELTA_FLASH_MS);
  }, []);

  // Clean up all pending flash timers on unmount.
  useEffect(() => {
    return () => {
      Object.values(flashTimersRef.current).forEach(clearTimeout);
    };
  }, []);

  // Connect WebSocket
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const candidates = [
      `${protocol}//${window.location.host}/api/world/agentverse/ws`,
      `${protocol}//${window.location.hostname}:8000/world/agentverse/ws`,
    ];

    let closed = false;
    let socket: WebSocket | null = null;
    let candidateIndex = 0;

    const connect = () => {
      const wsUrl = candidates[candidateIndex];
      addLog(`🔌 Connecting to ${wsUrl}`);
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        addLog(`🟢 Connected to AgentVerse via ${candidateIndex === 0 ? "proxy" : "backend"}`);
        wsRef.current = socket;
      };

      socket.onmessage = (event) => {
        let data: Record<string, unknown>;
        try { data = JSON.parse(event.data); } catch { return; }
        const type = data.type as string;

      if (type === "world_state" || type === "world_tick") {
        const payload = (data.data ?? data) as WorldState;
        setState(payload);
        setTick(payload.tick ?? 0);
        setBrains(Object.fromEntries((payload.agents ?? []).filter(a => a.brain).map(a => [a.agent_id, a.brain as BrainSnapshot])));
      } else if (type === "world_pulse") {
        const payload = data.state as WorldState;
        setState(payload);
        setTick((data.tick as number) ?? payload.tick ?? 0);
        setBrains(Object.fromEntries((payload.agents ?? []).filter(a => a.brain).map(a => [a.agent_id, a.brain as BrainSnapshot])));
      } else if (type === "world_ticker") {
        const status = data.status as WorldPulseStatus;
        setTickerStatus(status);
        if (typeof data.pace_seconds === "number") setPaceSeconds(data.pace_seconds);
        if (status === "crashed" && data.error) addLog(`💥 Ticker crashed: ${data.error}`);
      } else if (type === "agent_greeted") {
        appendInteraction({
          kind: "greeted", id: data.id as string,
          from: data.from as string, from_name: data.from_name as string,
          to_name: data.to_name as string, text: data.text as string,
          tick: (data.tick as number) ?? 0,
        });
      } else if (type === "agent_asked") {
        const from = data.from as string;
        appendInteraction({
          kind: "asked", id: data.id as string,
          from, from_name: data.from_name as string,
          to_name: data.to_name as string, text: data.text as string,
          tick: (data.tick as number) ?? 0,
        });
        flashDelta(from, ["asked"]);
      } else if (type === "agent_answered") {
        const from = data.from as string;
        appendInteraction({
          kind: "answered", id: data.id as string,
          from, from_name: data.from_name as string,
          to_name: data.to_name as string, text: data.text as string,
          tick: (data.tick as number) ?? 0,
        });
        flashDelta(from, ["answered"]);
      } else if (type === "agent_learned") {
        const agent = data.agent as string;
        const kindOf = data.kind_of as "skill" | "memory" | "knowledge";
        appendInteraction({
          kind: "learned", id: data.id as string,
          agent, agent_name: data.agent_name as string,
          detail: data.detail as string, kind_of: kindOf,
          tick: (data.tick as number) ?? 0,
        });
        flashDelta(agent, [kindOf === "memory" ? "memories" : "skills"]);
      } else if (type === "agent_spoke") {
        const msg = (data as { message: { sender_name: string; content: string } }).message;
        addLog(`💬 ${msg.sender_name}: "${msg.content.slice(0, 60)}..."`);
      } else if (type === "agent_spawned") {
        const a = (data as { agent: { name: string } }).agent;
        addLog(`🆕 Agent ${a.name} joined the world`);
      } else if (type === "agent_removed") {
        addLog(`🚫 Agent ${(data as { agent_id: string }).agent_id} left the world`);
      }
    };

      socket.onclose = () => {
        if (closed) return;
        if (candidateIndex === 0) {
          addLog("🟡 Proxy WebSocket failed — retrying direct backend...");
          candidateIndex = 1;
          connect();
          return;
        }
        addLog("🔴 Disconnected");
      };

      socket.onerror = () => {
        addLog(`❌ WebSocket error on ${candidateIndex === 0 ? "proxy" : "backend"}`);
      };
    };

    connect();

    return () => {
      closed = true;
      socket?.close();
    };
  }, [addLog, appendInteraction, flashDelta]);

  // Canvas drawing (unchanged from the previous version, kept intact)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !state) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const scale = canvas.width / WORLD_SIZE;

    ctx.fillStyle = BG_COLOR;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = GRID_COLOR;
    ctx.lineWidth = 1;
    for (let i = 0; i <= WORLD_SIZE; i += 50) {
      ctx.beginPath(); ctx.moveTo(i * scale, 0); ctx.lineTo(i * scale, canvas.height); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i * scale); ctx.lineTo(canvas.width, i * scale); ctx.stroke();
    }

    state.locations.forEach((loc) => {
      const x = loc.position.x * scale, y = loc.position.y * scale;
      ctx.fillStyle = "#22c55e40"; ctx.strokeStyle = "#22c55e"; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(x, y, 20 * scale, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      ctx.fillStyle = "#22c55e"; ctx.font = `${11 * scale}px sans-serif`; ctx.textAlign = "center";
      ctx.fillText(loc.name, x, y - 28 * scale);
      const icons: Record<string, string> = { market: "🏪", library: "📚", workshop: "🔧", lab: "🔬", general: "🏛️" };
      ctx.font = `${16 * scale}px sans-serif`;
      ctx.fillText(icons[loc.type] || "📍", x, y + 6 * scale);
    });

    ctx.lineWidth = 1; ctx.setLineDash([3, 3]);
    state.agents.forEach((a) => {
      state.agents.forEach((b) => {
        if (a.agent_id < b.agent_id) {
          const dx = a.position.x - b.position.x, dy = a.position.y - b.position.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.strokeStyle = `${AGENT_COLORS[a.agent_id] || "#8b5cf6"}40`;
            ctx.beginPath();
            ctx.moveTo(a.position.x * scale, a.position.y * scale);
            ctx.lineTo(b.position.x * scale, b.position.y * scale);
            ctx.stroke();
          }
        }
      });
    });
    ctx.setLineDash([]);

    state.agents.forEach((agent) => {
      const x = agent.position.x * scale, y = agent.position.y * scale;
      const color = AGENT_COLORS[agent.agent_id] || "#8b5cf6";
      const radius = 14 * scale;

      const glow = ctx.createRadialGradient(x, y, 0, x, y, radius * 2);
      glow.addColorStop(0, `${color}60`); glow.addColorStop(1, "transparent");
      ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(x, y, radius * 2, 0, Math.PI * 2); ctx.fill();

      ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2); ctx.fill();

      if (agent.energy < 100) {
        ctx.fillStyle = "#333"; ctx.fillRect(x - radius, y + radius + 4, radius * 2, 3);
        ctx.fillStyle = agent.energy > 50 ? "#22c55e" : agent.energy > 25 ? "#f59e0b" : "#ef4444";
        ctx.fillRect(x - radius, y + radius + 4, radius * 2 * (agent.energy / 100), 3);
      }

      ctx.fillStyle = "#fff"; ctx.font = `bold ${11 * scale}px sans-serif`; ctx.textAlign = "center";
      ctx.fillText(agent.name, x, y - radius - 8 * scale);

      const stateDots: Record<string, string> = { idle: "#6b7280", moving: "#3b82f6", working: "#f59e0b", talking: "#22c55e", listening: "#8b5cf6", sleeping: "#9ca3af" };
      ctx.fillStyle = stateDots[agent.state] || "#6b7280";
      ctx.beginPath(); ctx.arc(x + radius + 4 * scale, y - radius + 4 * scale, 3 * scale, 0, Math.PI * 2); ctx.fill();
    });

    state.active_messages.forEach((msg) => {
      const sender = state.agents.find((a) => a.name === msg.sender_name);
      if (!sender) return;
      const x = sender.position.x * scale, y = sender.position.y * scale - 25 * scale;
      ctx.fillStyle = "#ffffff20"; ctx.strokeStyle = "#ffffff40"; ctx.lineWidth = 1;
      const tw = ctx.measureText(msg.content.slice(0, 30)).width;
      const bw = Math.max(60, tw + 20), bh = 24, bx = x - bw / 2, by = y - bh - 8;
      ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 6); ctx.fill(); ctx.stroke();
      ctx.fillStyle = "#fff"; ctx.font = `${10 * scale}px sans-serif`; ctx.textAlign = "center";
      ctx.fillText(msg.content.slice(0, 30), x, y - bh + bh / 2 + 3.5 * scale);
    });
  }, [state]);

  const sendCommand = useCallback((action: string, data: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, ...data }));
    }
  }, []);

  const startLiving = () => sendCommand("start", { pace_seconds: paceSeconds });
  const pauseLiving = () => sendCommand("pause");
  const onPaceChange = (v: number) => {
    setPaceSeconds(v);
    sendCommand("set_pace", { pace_seconds: v });
  };
  const burst60 = () => sendCommand("tick", { count: 60 });

  const agentList = useMemo(
    () => (state?.agents ?? []).map((a) => ({ agent_id: a.agent_id, name: a.name })),
    [state?.agents],
  );

  return (
    <div className="p-4" dir="ltr">
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-white">🌍 AgentVerse</h1>
          <p className="text-zinc-400 text-xs">
            {state ? `${state.agents.length} agents · ${state.locations.length} locations` : "Connecting..."}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {tickerStatus === "running" ? (
            <button onClick={pauseLiving}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-sm font-medium transition-colors">
              ⏸ Pause
            </button>
          ) : (
            <button onClick={startLiving}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors">
              ▶ Start Living
            </button>
          )}
          <label className="flex items-center gap-2 text-xs text-zinc-400 bg-zinc-900/60 border border-zinc-800 rounded-lg px-2 py-1.5">
            <span>pace</span>
            <input
              type="range" min={1} max={10} step={0.5}
              value={paceSeconds}
              onChange={(e) => onPaceChange(parseFloat(e.target.value))}
              className="w-28"
            />
            <span className="tabular-nums w-10 text-right text-white">{paceSeconds.toFixed(1)}s</span>
          </label>
          <button onClick={burst60}
            className="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm transition-colors">
            ▶️ Burst 60
          </button>
          <button onClick={() => sendCommand("tick", { count: 1 })}
            className="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm transition-colors">
            ⏭️ Tick
          </button>
        </div>
      </div>

      <div className="grid grid-cols-[660px,minmax(0,1fr)] gap-4">
        {/* Left: canvas */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
          <canvas ref={canvasRef} width={660} height={660} className="block" />
        </div>

        {/* Right: pulse + interactions + learning cards */}
        <div className="flex flex-col gap-3 min-w-0">
          <WorldPulse
            tick={tick}
            status={tickerStatus}
            paceSeconds={paceSeconds}
            uptimeSeconds={state?.stats?.uptime_seconds ?? 0}
            agentCount={state?.stats?.total_agents ?? 0}
            totalInteractions={state?.stats?.total_interactions ?? 0}
            totalLearnings={state?.stats?.total_learnings ?? 0}
          />

          <div className="h-72">
            <InteractionStream events={interactionEvents} agentColors={AGENT_COLORS} />
          </div>

          <AgentLearningCards
            agents={agentList}
            brains={brains}
            recentDeltas={recentDeltas}
            agentColors={AGENT_COLORS}
          />

          {/* Companies + event log (kept for parity with old page) */}
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-3">
            <h2 className="text-white font-semibold text-sm mb-2">🏢 Companies</h2>
            <div className="space-y-1">
              {state?.companies?.map((c) => (
                <div key={c.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COMPANY_COLORS[c.name] || "#8b5cf6" }} />
                    <span className="text-white">{c.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${c.status === "busy" ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-700 text-zinc-400"}`}>
                      {c.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-zinc-500">
                    <span>👥{c.employees.length}</span>
                    <span>✅{c.completed_tasks}</span>
                    <span>💰${c.revenue.toFixed(1)}</span>
                  </div>
                </div>
              ))}
              {(!state?.companies || state.companies.length === 0) && (
                <p className="text-zinc-600 text-xs">No companies yet</p>
              )}
            </div>
          </div>

          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-3">
            <h2 className="text-white font-semibold text-sm mb-2">📜 Event Log</h2>
            <div className="h-40 overflow-y-auto space-y-0.5 text-xs font-mono">
              {log.length === 0 ? (
                <p className="text-zinc-600">Waiting for events...</p>
              ) : (
                log.map((entry, i) => <p key={i} className="text-zinc-400">{entry}</p>)
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
