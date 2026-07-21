"use client";

import { useEffect, useRef, useState, useCallback } from "react";

type Agent = { agent_id: string; name: string; position: { x: number; y: number }; state: string; energy: number; skills: string[]; discovered: number; messages_sent: number; messages_received: number };
type Location = { id: string; name: string; position: { x: number; y: number }; type: string };
type Message = { message_id: string; sender_name: string; content: string; target: string };
type WorldState = { name: string; width: number; height: number; agents: Agent[]; locations: Location[]; active_messages: Message[]; companies?: Company[] };
type Company = { name: string; description: string; position: { x: number; y: number }; employees: string[]; completed_tasks: number; revenue: number; status: string };

const COMPANY_COLORS: Record<string, string> = {
  "Agent-Flow": "#8b5cf6",
  "VirtualCorp": "#06b6d4",
  "Hermes Brain": "#f43f5e",
  "DataSphere": "#22c55e",
};

const WORLD_SIZE = 300;
const BG_COLOR = "#0f0f23";
const GRID_COLOR = "#1a1a3e";
const AGENT_COLORS: Record<string, string> = { "agent-1": "#8b5cf6", "agent-2": "#06b6d4", "agent-3": "#f43f5e" };

export default function WorldPage() {
  const [state, setState] = useState<WorldState | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [ticking, setTicking] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Connect WebSocket
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.hostname}:8000/world/agentverse/ws`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      addLog("🟢 Connected to AgentVerse");
      setWs(socket);
      wsRef.current = socket;
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "world_state" || data.type === "world_tick") {
        setState(data.data);
      } else if (data.type === "agent_spoke") {
        addLog(`💬 ${data.message.sender_name}: "${data.message.content.slice(0, 60)}..."`);
      } else if (data.type === "agent_spawned") {
        addLog(`🆕 Agent ${data.agent.name} joined the world`);
      } else if (data.type === "agent_removed") {
        addLog(`🚫 Agent ${data.agent_id} left the world`);
      } else if (data.type === "agent_moved") {
        // Agent moved - visual only
      }
    };

    socket.onclose = () => addLog("🔴 Disconnected");
    socket.onerror = () => addLog("❌ WebSocket error");

    return () => socket.close();
  }, []);

  const addLog = (msg: string) => {
    setLog((prev) => [...prev.slice(-49), `${new Date().toLocaleTimeString()} ${msg}`]);
  };

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !state) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const scale = canvas.width / WORLD_SIZE;

    // Background
    ctx.fillStyle = BG_COLOR;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Grid
    ctx.strokeStyle = GRID_COLOR;
    ctx.lineWidth = 1;
    for (let i = 0; i <= WORLD_SIZE; i += 50) {
      ctx.beginPath();
      ctx.moveTo(i * scale, 0);
      ctx.lineTo(i * scale, canvas.height);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i * scale);
      ctx.lineTo(canvas.width, i * scale);
      ctx.stroke();
    }

    // Locations
    state.locations.forEach((loc) => {
      const x = loc.position.x * scale;
      const y = loc.position.y * scale;
      ctx.fillStyle = "#22c55e40";
      ctx.strokeStyle = "#22c55e";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x, y, 20 * scale, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#22c55e";
      ctx.font = `${11 * scale}px sans-serif`;
      ctx.textAlign = "center";
      ctx.fillText(loc.name, x, y - 28 * scale);
      const icons: Record<string, string> = { market: "🏪", library: "📚", workshop: "🔧", lab: "🔬", general: "🏛️" };
      ctx.font = `${16 * scale}px sans-serif`;
      ctx.fillText(icons[loc.type] || "📍", x, y + 6 * scale);
    });

    // Connection lines between nearby agents
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    state.agents.forEach((a) => {
      state.agents.forEach((b) => {
        if (a.agent_id < b.agent_id) {
          const dx = a.position.x - b.position.x;
          const dy = a.position.y - b.position.y;
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

    // Agents
    state.agents.forEach((agent) => {
      const x = agent.position.x * scale;
      const y = agent.position.y * scale;
      const color = AGENT_COLORS[agent.agent_id] || "#8b5cf6";
      const radius = 14 * scale;

      // Glow
      const glow = ctx.createRadialGradient(x, y, 0, x, y, radius * 2);
      glow.addColorStop(0, `${color}60`);
      glow.addColorStop(1, "transparent");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(x, y, radius * 2, 0, Math.PI * 2);
      ctx.fill();

      // Body
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fill();

      // Energy bar
      if (agent.energy < 100) {
        ctx.fillStyle = "#333";
        ctx.fillRect(x - radius, y + radius + 4, radius * 2, 3);
        ctx.fillStyle = agent.energy > 50 ? "#22c55e" : agent.energy > 25 ? "#f59e0b" : "#ef4444";
        ctx.fillRect(x - radius, y + radius + 4, radius * 2 * (agent.energy / 100), 3);
      }

      // Name
      ctx.fillStyle = "#fff";
      ctx.font = `bold ${11 * scale}px sans-serif`;
      ctx.textAlign = "center";
      ctx.fillText(agent.name, x, y - radius - 8 * scale);

      // State indicator
      const stateDots: Record<string, string> = { idle: "#6b7280", moving: "#3b82f6", working: "#f59e0b", talking: "#22c55e", listening: "#8b5cf6", sleeping: "#9ca3af" };
      ctx.fillStyle = stateDots[agent.state] || "#6b7280";
      ctx.beginPath();
      ctx.arc(x + radius + 4 * scale, y - radius + 4 * scale, 3 * scale, 0, Math.PI * 2);
      ctx.fill();
    });

    // Speech bubbles
    state.active_messages.forEach((msg) => {
      const sender = state.agents.find((a) => a.name === msg.sender_name);
      if (!sender) return;
      const x = sender.position.x * scale;
      const y = sender.position.y * scale - 25 * scale;

      ctx.fillStyle = "#ffffff20";
      ctx.strokeStyle = "#ffffff40";
      ctx.lineWidth = 1;
      const tw = ctx.measureText(msg.content.slice(0, 30)).width;
      const bw = Math.max(60, tw + 20);
      const bh = 24;
      const bx = x - bw / 2;
      const by = y - bh - 8;

      // Bubble
      ctx.beginPath();
      ctx.roundRect(bx, by, bw, bh, 6);
      ctx.fill();
      ctx.stroke();

      // Text
      ctx.fillStyle = "#fff";
      ctx.font = `${10 * scale}px sans-serif`;
      ctx.textAlign = "center";
      ctx.fillText(msg.content.slice(0, 30), x, y - bh + bh / 2 + 3.5 * scale);
    });
  }, [state]);

  const sendCommand = useCallback((action: string, data: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, ...data }));
    }
  }, []);

  const runTicks = () => {
    setTicking(true);
    sendCommand("tick", { count: 20 });
    setTimeout(() => {
      sendCommand("tick", { count: 20 });
      setTimeout(() => {
        sendCommand("tick", { count: 20 });
        setTicking(false);
      }, 2000);
    }, 2000);
  };

  return (
    <div className="p-4" dir="ltr">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-white">🌍 AgentVerse</h1>
          <p className="text-zinc-400 text-xs">
            {state ? `${state.agents.length} agents · ${state.locations.length} locations` : "Connecting..."}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={runTicks}
            disabled={ticking}
            className="px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {ticking ? "⏳ Running..." : "▶️ Run World (60 ticks)"}
          </button>
          <button
            onClick={() => sendCommand("tick", { count: 1 })}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm transition-colors"
          >
            ⏭️ Tick
          </button>
        </div>
      </div>

      <div className="flex gap-4">
        {/* Canvas */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden flex-shrink-0">
          <canvas
            ref={canvasRef}
            width={660}
            height={660}
            className="block"
          />
        </div>

        {/* Side panel */}
        <div className="flex-1 space-y-4 min-w-0">
          {/* Agents */}
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
            <h2 className="text-white font-semibold text-sm mb-3">🤖 Agents</h2>
            <div className="space-y-2">
              {state?.agents.map((a) => (
                <div key={a.agent_id} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: AGENT_COLORS[a.agent_id] || "#8b5cf6" }} />
                    <span className="text-white text-sm">{a.name}</span>
                    <span className="text-zinc-500 text-xs capitalize">{a.state}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-zinc-500">
                    <span>⚡{a.energy.toFixed(0)}</span>
                    <span>📤{a.messages_sent}</span>
                    <span>📥{a.messages_received}</span>
                    <span>👀{a.discovered}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Companies */}
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
            <h2 className="text-white font-semibold text-sm mb-3">🏢 Companies</h2>
            <div className="space-y-2">
              {state?.companies?.map((c) => (
                <div key={c.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COMPANY_COLORS[c.name] || "#8b5cf6" }} />
                    <span className="text-white text-sm">{c.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      c.status === "busy" ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-700 text-zinc-400"
                    }`}>
                      {c.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-zinc-500">
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

          {/* Event log */}
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
            <h2 className="text-white font-semibold text-sm mb-3">📜 Event Log</h2>
            <div ref={logRef} className="h-64 overflow-y-auto space-y-0.5 text-xs font-mono">
              {log.length === 0 ? (
                <p className="text-zinc-600">Waiting for events...</p>
              ) : (
                log.map((entry, i) => (
                  <p key={i} className="text-zinc-400">
                    {entry}
                  </p>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}