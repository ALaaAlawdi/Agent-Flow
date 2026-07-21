🧠 **A skill for your coding agent that stops burying the answer**

Just came across **ayghri/i-have-adhd** (5k+ stars, MIT) via Eduardo Ordax's post — and the framing is sharper than the joke name suggests.

The repo's premise is simple but the engineering insight is real:

> Coding agents default to *chat-mode* output — preamble, hedging, "Hope this helps!", recaps. That format is wrong for an agent that lives inside a terminal.

The skill ships 10 output rules for Claude Code / Codex / Cursor:

1. Lead with the next action
2. Number multi-step tasks
3. End with one concrete next step
4. Suppress tangents
5. Restate state every turn
6. Specific time estimates (minutes, not "a bit")
7. Make wins visible
8. Matter-of-fact errors
9. Cap lists at 5 items
10. No preamble, recap, or closers

━━━━━━━━━━━━━━━━━━━━

**The mental model most agent builders have:**
"Make the agent smarter."
But if the agent's output is unreadable in a terminal at 2am during an incident, smart doesn't matter — *actionable* matters.

**The problem it actually solves:**
Agent UX in the CLI is mostly *output-shape* UX. The model is the same; the system prompt around it is what changes whether the human can act on what comes back.

━━━━━━━━━━━━━━━━━━━━

**Why this matters in production:**

Before → 6 lines of preamble before the actual command, plus 3 lines of "Hope this helps!" after.

After → "Run `npm install jsonwebtoken@latest`, then edit `src/auth.ts:42`. Next: paste the first failing line."

Same model. Same context. Different *skill wrapping the output*. The agent just becomes usable.

━━━━━━━━━━━━━━━━━━━━

**The architecture I like:**

The project ships as a Claude Code / Codex **plugin** (not a model fine-tune, not a new agent framework):

• `claude plugin marketplace add ayghri/i-have-adhd`
• `claude plugin install i-have-adhd@i-have-adhd`
• Invoke with `/i-have-adhd`

You fork it, edit `SKILL.md`, and tune the rules for your team's voice. No Python, no API keys, no waiting on a vendor.

━━━━━━━━━━━━━━━━━━━━

**The honest limitation:**

This is a **presentation skill**, not a reasoning skill. It does not make the agent more correct — it makes correct output *actable*. For complex multi-step bugs where the model itself needs to think harder, you want reasoning models (o1, extended thinking) on top of this, not instead of it.

Also: any output-formatting skill inherits the agent's underlying verbosity. If your model still fills half the context with thinking tokens, you're paying for "skill-shaped" output but losing elsewhere.

━━━━━━━━━━━━━━━━━━━━

**Engineering takeaway:**
Most "my coding agent is annoying" complaints are actually *output-shape* complaints, not capability complaints. Try a presentation skill before swapping models.

**Question for the community:**
For those running agents in production — have you shipped a custom skill/SKILL.md to tune agent output for your team's workflow? What rules stuck and which ones did the model just ignore?

━━━━━━━━━━━━━━━━━━━━

🔗 Repo: https://github.com/ayghri/i-have-adhd
📦 Install: `claude plugin install i-have-adhd@i-have-adhd`
📄 Rules: `skills/i-have-adhd/SKILL.md`
👤 Shared by: Eduardo Ordax (https://www.linkedin.com/in/eordax)

#ClaudeCode #AIagents #DeveloperTools #Productivity #LLM