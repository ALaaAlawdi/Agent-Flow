"use client";

import { useState } from "react";

const PRICING = [
  {
    name: "Starter",
    price: "29",
    agents: "3",
    calls: "1,000",
    features: ["3 AI Agents", "1,000 API Calls/mo", "Web + File Tools", "Basic Support"],
    cta: "Start Free Trial",
    highlight: false,
  },
  {
    name: "Pro",
    price: "99",
    agents: "10",
    calls: "10,000",
    features: ["10 AI Agents", "10,000 API Calls/mo", "All Tools", "Priority Support", "Custom Skills", "Team Collaboration"],
    cta: "Get Pro",
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "499",
    agents: "∞",
    calls: "∞",
    features: ["Unlimited Agents", "Unlimited API Calls", "All Tools + Custom", "Dedicated Support", "On-Premise Option", "SLA Guarantee", "Custom Integrations"],
    cta: "Contact Sales",
    highlight: false,
  },
];

const STATS = [
  { value: "218K", label: "Hermes Stars" },
  { value: "65+", label: "API Endpoints" },
  { value: "4", label: "Agent Types" },
  { value: "29", label: "Tests Passing" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#08081a]" dir="ltr">
      {/* Hero */}
      <section className="text-center px-6 pt-24 pb-16">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-xs mb-6">
          🚀 Powered by DeepSeek v4-pro
        </div>
        <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
          <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-cyan-400 bg-clip-text text-transparent">
            Hire AI Agents
          </span>
          <br />
          <span className="text-white">Not Employees</span>
        </h1>
        <p className="text-zinc-400 text-lg max-w-2xl mx-auto mb-8 leading-relaxed">
          Agent-Flow is an open-source platform that lets you build, deploy, and manage teams of AI agents. 
          They research, code, review, and document — automatically. Powered by Hermes Agent's learning loop.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <a href="/brain/" className="px-8 py-3.5 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white rounded-xl font-semibold text-sm shadow-lg shadow-violet-500/25 transition-all">
            🧠 Try Live Demo
          </a>
          <a href="https://github.com/ALaaAlawdi/Agent-Flow" target="_blank" className="px-8 py-3.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl font-semibold text-sm border border-zinc-700 transition-all">
            ⭐ GitHub
          </a>
        </div>
      </section>

      {/* Stats */}
      <section className="max-w-4xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {STATS.map((s) => (
            <div key={s.label} className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-5 text-center">
              <p className="text-3xl font-bold text-white mb-1">{s.value}</p>
              <p className="text-zinc-500 text-xs">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-5xl mx-auto px-6 pb-20">
        <h2 className="text-2xl font-bold text-white text-center mb-12">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { emoji: "📝", title: "Send a Task", desc: "One API call. One message. Any language." },
            { emoji: "🧠", title: "Brain Routes It", desc: "Auto-assigns to the right agent." },
            { emoji: "🤖", title: "Agent Executes", desc: "Researcher → Coder → Reviewer → Writer." },
            { emoji: "✅", title: "Verified Output", desc: "Auto-reviewed. Always checked." },
          ].map((step, i) => (
            <div key={i} className="bg-zinc-900/30 border border-zinc-800/50 rounded-2xl p-6 text-center">
              <p className="text-3xl mb-3">{step.emoji}</p>
              <h3 className="text-white font-semibold text-sm mb-2">{step.title}</h3>
              <p className="text-zinc-500 text-xs leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Agent Types */}
      <section className="max-w-5xl mx-auto px-6 pb-20">
        <h2 className="text-2xl font-bold text-white text-center mb-8">Your AI Team</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { emoji: "🔍", name: "Researcher", color: "violet", desc: "Finds facts, analyzes data" },
            { emoji: "💻", name: "Developer", color: "cyan", desc: "Writes code, builds features" },
            { emoji: "🔎", name: "Reviewer", color: "rose", desc: "Checks quality, finds bugs" },
            { emoji: "📝", name: "Writer", color: "emerald", desc: "Documents, explains, translates" },
          ].map((a) => (
            <div key={a.name} className="bg-zinc-900/30 border border-zinc-800 rounded-2xl p-5 text-center">
              <p className="text-2xl mb-2">{a.emoji}</p>
              <p className="text-white font-semibold text-sm">{a.name}</p>
              <p className="text-zinc-500 text-xs">{a.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-5xl mx-auto px-6 pb-20">
        <h2 className="text-2xl font-bold text-white text-center mb-4">Pricing</h2>
        <p className="text-zinc-500 text-sm text-center mb-10">Start free. Scale when you're ready.</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {PRICING.map((plan) => (
            <div key={plan.name} className={`relative rounded-2xl p-6 border ${plan.highlight ? "border-violet-500/50 bg-violet-500/5 ring-1 ring-violet-500/20" : "border-zinc-800 bg-zinc-900/30"}`}>
              {plan.highlight && <p className="absolute -top-3 left-1/2 -translate-x-1/2 bg-violet-600 text-white text-xs px-3 py-1 rounded-full font-semibold">Most Popular</p>}
              <h3 className="text-white font-semibold mb-1">{plan.name}</h3>
              <p className="text-3xl font-bold text-white mb-4">${plan.price}<span className="text-zinc-500 text-sm font-normal">/mo</span></p>
              <div className="flex gap-4 text-xs text-zinc-400 mb-4">
                <span>{plan.agents} agents</span>
                <span>{plan.calls} calls</span>
              </div>
              <ul className="space-y-2 mb-6">
                {plan.features.map((f) => (
                  <li key={f} className="text-zinc-400 text-xs flex items-center gap-2">
                    <span className="text-emerald-400">✓</span> {f}
                  </li>
                ))}
              </ul>
              <button className={`w-full py-2.5 rounded-xl text-sm font-semibold transition-all ${plan.highlight ? "bg-violet-600 hover:bg-violet-500 text-white" : "bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700"}`}>
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="text-center px-6 pb-24">
        <h2 className="text-3xl font-bold text-white mb-4">Ready to hire your AI team?</h2>
        <p className="text-zinc-400 mb-8">Open source. Self-hosted. Production ready.</p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <a href="/brain/" className="px-8 py-3.5 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-xl font-semibold text-sm shadow-lg shadow-violet-500/25">
            🧠 Try Free Demo
          </a>
          <a href="https://github.com/ALaaAlawdi/Agent-Flow" target="_blank" className="px-8 py-3.5 bg-zinc-800 text-white rounded-xl font-semibold text-sm border border-zinc-700">
            ⭐ Star on GitHub
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="text-center pb-8 text-zinc-600 text-xs">
        Agent-Flow v0.2.0 · Open Source · Powered by DeepSeek & Hermes Agent
      </footer>
    </div>
  );
}