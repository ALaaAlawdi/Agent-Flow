"use client";

import { useEffect, useRef } from "react";

export type InteractionEventKind = "greeted" | "asked" | "answered" | "learned";
export type InteractionEvent =
  | { kind: "greeted";  id: string; from: string; from_name: string; to_name: string; text: string; tick: number }
  | { kind: "asked";    id: string; from: string; from_name: string; to_name: string; text: string; tick: number }
  | { kind: "answered"; id: string; from: string; from_name: string; to_name: string; text: string; tick: number }
  | { kind: "learned";  id: string; agent: string; agent_name: string; detail: string; kind_of: "skill"|"memory"|"knowledge"; tick: number };

export type InteractionStreamProps = {
  events: InteractionEvent[];
  agentColors: Record<string, string>;
};

const KIND_ICON: Record<InteractionEventKind, string> = {
  greeted:  "👋",
  asked:    "🙋",
  answered: "💬",
  learned:  "✨",
};

const LEARN_ICON: Record<"skill" | "memory" | "knowledge", string> = {
  skill:     "🛠",
  memory:    "🤝",
  knowledge: "📖",
};

function renderRow(ev: InteractionEvent, agentColors: Record<string, string>) {
  const actor = ev.kind === "learned" ? ev.agent : ev.from;
  const color = agentColors[actor] ?? "#8b5cf6";
  const icon = ev.kind === "learned" ? LEARN_ICON[ev.kind_of] : KIND_ICON[ev.kind];

  let body: React.ReactNode;
  switch (ev.kind) {
    case "greeted":
      body = <><span className="text-white">{ev.from_name}</span><span className="text-zinc-500"> → </span><span className="text-white">{ev.to_name}</span>: <span className="text-zinc-300">{ev.text}</span></>;
      break;
    case "asked":
      body = <><span className="text-white">{ev.from_name}</span><span className="text-zinc-500"> asks </span><span className="text-white">{ev.to_name}</span>: <span className="text-amber-300">"{ev.text}"</span></>;
      break;
    case "answered":
      body = <><span className="text-white">{ev.from_name}</span><span className="text-zinc-500"> answers </span><span className="text-white">{ev.to_name}</span>: <span className="text-emerald-300">"{ev.text}"</span></>;
      break;
    case "learned":
      body = <><span className="text-white">{ev.agent_name}</span><span className="text-zinc-500"> learned </span><span className="text-violet-300">{ev.detail}</span></>;
      break;
  }

  return (
    <div key={ev.id} className="lv-slide-in flex items-start gap-2 text-xs py-1 px-2 border-b border-zinc-900/60">
      <span className="inline-block h-2 w-2 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: color }} />
      <span className="w-4 flex-shrink-0 text-center" aria-hidden>{icon}</span>
      <span className="text-zinc-400 tabular-nums flex-shrink-0">t{ev.tick}</span>
      <span className="flex-1 min-w-0 break-words">{body}</span>
    </div>
  );
}

export default function InteractionStream({ events, agentColors }: InteractionStreamProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const atBottomRef = useRef(true);

  const onScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    atBottomRef.current = nearBottom;
  };

  useEffect(() => {
    if (atBottomRef.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events[events.length - 1]?.id]);

  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-2 h-full flex flex-col">
      <div className="text-white font-semibold text-sm px-2 pb-2">💭 Interactions</div>
      <div
        ref={scrollRef}
        onScroll={onScroll}
        className="flex-1 overflow-y-auto min-h-0 rounded-lg"
      >
        {events.length === 0 ? (
          <p className="text-zinc-600 text-xs px-3 py-6 text-center animate-pulse">
            Waiting for the world to come alive...
          </p>
        ) : (
          events.map((e) => renderRow(e, agentColors))
        )}
      </div>
    </div>
  );
}
