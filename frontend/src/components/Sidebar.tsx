"use client";

import { Bot, Brain, Globe, LayoutDashboard, Play, BarChart3, Settings, Wrench, Menu, X, BriefcaseBusiness } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/" },
  { icon: Wrench, label: "Alook", href: "/alook" },
  { icon: Wrench, label: "Job Hunter", href: "/job-hunter" },
  { icon: Wrench, label: "Brain Chat", href: "/brain-chat" },
  { icon: Wrench, label: "Hermes Tools", href: "/hermes-tools" },
  { icon: BriefcaseBusiness, label: "Missions", href: "/missions" },
  { icon: Brain, label: "Human Agents", href: "/human-agents" },
  { icon: Brain, label: "Hermes Agents", href: "/hermes-agents" },
  { icon: Globe, label: "AgentVerse", href: "/world" },
  { icon: Play, label: "Scenarios", href: "/scenarios" },
  { icon: Bot, label: "Teams", href: "/teams" },
  { icon: BarChart3, label: "Analytics", href: "/analytics" },
  { icon: Settings, label: "Settings", href: "/settings" },
];

export default function Sidebar() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Mobile hamburger */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed top-4 left-4 z-[60] p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 lg:hidden"
      >
        {open ? <X className="w-5 h-5 text-white" /> : <Menu className="w-5 h-5 text-white" />}
      </button>

      {/* Overlay for mobile */}
      {open && (
        <div
          onClick={() => setOpen(false)}
          className="fixed inset-0 bg-black/60 z-[55] lg:hidden"
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-full w-64 bg-zinc-900 border-r border-zinc-800 p-4 z-50 transition-transform lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-bold text-sm">
            AF
          </div>
          <div>
            <h1 className="text-white font-semibold text-sm">Agent-Flow</h1>
            <p className="text-zinc-500 text-xs">v0.2.0</p>
          </div>
        </div>

        <nav className="space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors text-sm"
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-zinc-800/50 rounded-lg p-3 border border-zinc-700/50">
            <p className="text-xs text-zinc-500 mb-1">API Status</p>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-emerald-400 text-xs font-medium">Connected</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}