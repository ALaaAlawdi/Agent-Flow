const API_BASE = "/api";

export type Team = { name: string; goal: string; created_at: string; };
export type Scenario = { scenario_id: string; title: string; description: string; icon: string; category: string; team_size: number; step_count: number; estimated_time: string; };
export type ScenarioResult = { scenario_id: string; title: string; team_name: string; agents_added: string[]; steps_executed: number; successful_steps: number; stats: { interactions: { total_interactions: number; unique_types: number }; active_agents: { agent_id: string; interactions: number }[] }; };

export type Agent = { name: string; role: string; model: string; status: string; };
export type Task = { id: string; description: string; status: string; assigned_to: string; created_at: string; };
export type Knowledge = { id: string; content: string; source: string; confidence: string; };
export type Memory = { key: string; value: string; timestamp: string; };
export type Interaction = { interaction_id: string; type: string; source: string | null; target: string | null; summary: string; timestamp: string; data: Record<string, unknown>; };
export type Conversation = { id: string; participants: string[]; messages: { role: string; content: string }[]; };
export type Workflow = { id: string; name: string; steps: number; status: string; };

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export const api = {
  health: () => fetchApi<{ status: string }>("/health"),
  status: () => fetchApi<Record<string, unknown>>("/status"),

  // Models
  listModels: () => fetchApi<{ models: { short_name: string; provider: string }[] }>("/models"),
  defaultModel: () => fetchApi<{ model: string; provider: string }>("/models/default"),

  // Scenarios
  listScenarios: () => fetchApi<{ scenarios: Scenario[] }>("/scenarios"),
  getScenario: (id: string) => fetchApi<Scenario & { team_config: Record<string, unknown> }>(`/scenarios/${id}`),
  runScenario: (id: string) => fetchApi<ScenarioResult>(`/scenarios/${id}/run`, { method: "POST" }),

  // Teams
  listTeams: () => fetchApi<{ teams: Team[] }>("/teams"),
  getTeam: (name: string) => fetchApi<Team & { agents: Agent[] }>(`/teams/${name}`),
  createTeam: (name: string, goal: string) => fetchApi<Team>(`/teams`, { method: "POST", body: JSON.stringify({ name, goal }) }),

  // Agents
  addAgent: (team: string, name: string, role: string) => fetchApi<Agent>(`/teams/${team}/agents`, { method: "POST", body: JSON.stringify({ name, role }) }),
  runAgent: (team: string, description: string) => fetchApi<{ result: string }>(`/teams/${team}/run`, { method: "POST", body: JSON.stringify({ description }) }),
  broadcast: (team: string, message: string) => fetchApi<{ results: string[] }>(`/teams/${team}/broadcast`, { method: "POST", body: JSON.stringify({ message }) }),
  autonomous: (team: string, autonomous: boolean) => fetchApi<{ status: string }>(`/teams/${team}/autonomous`, { method: "POST", body: JSON.stringify({ autonomous }) }),

  // Knowledge
  getKnowledge: (team: string, query: string) => fetchApi<{ results: Knowledge[] }>(`/teams/${team}/knowledge`, { method: "POST", body: JSON.stringify({ query }) }),
  learn: (team: string, content: string) => fetchApi<{ result: string }>(`/teams/${team}/learning/record`, { method: "POST", body: JSON.stringify({ content }) }),
  getSuggestions: (team: string) => fetchApi<{ suggestions: string[] }>(`/teams/${team}/learning/suggestions`),
  autoImprove: (team: string) => fetchApi<{ result: string }>(`/teams/${team}/learning/auto-improve`, { method: "POST" }),

  // Queue
  getQueueStats: (team: string) => fetchApi<{ pending: number; completed: number; failed: number }>(`/teams/${team}/queue/stats`),
  addTask: (team: string, description: string, priority: number) => fetchApi<Task>(`/teams/${team}/queue/tasks`, { method: "POST", body: JSON.stringify({ description, priority }) }),
  nextTask: (team: string) => fetchApi<Task | null>(`/teams/${team}/queue/tasks/next`),
  completeTask: (team: string, taskId: string, result: string) => fetchApi<{ status: string }>(`/teams/${team}/queue/tasks/${taskId}/complete`, { method: "POST", body: JSON.stringify({ result }) }),

  // Conversations
  startConversation: (team: string, participants: string[], initial: string) => fetchApi<Conversation>(`/teams/${team}/conversations`, { method: "POST", body: JSON.stringify({ participants, initial_message: initial }) }),
  getConversation: (team: string, convId: string) => fetchApi<Conversation>(`/teams/${team}/conversations/${convId}`),
  sendMessage: (team: string, convId: string, role: string, content: string) => fetchApi<{ message: string }>(`/teams/${team}/conversations/${convId}/messages`, { method: "POST", body: JSON.stringify({ role, content }) }),

  // Interactions
  getInteractions: (team: string, limit = 50) => fetchApi<{ interactions: Interaction[] }>(`/teams/${team}/interactions?limit=${limit}`),
  getInteractionStats: (team: string) => fetchApi<{ total_interactions: number; by_type: Record<string, number>; unique_types: number }>(`/teams/${team}/interactions/stats`),
  getActiveAgents: (team: string) => fetchApi<{ active_agents: { agent_id: string; interactions: number }[] }>(`/teams/${team}/interactions/active-agents`),
  getTimeline: (team: string, since?: string) => fetchApi<{ timeline: { timestamp: string; event: string }[] }>(`/teams/${team}/timeline${since ? `?since=${since}` : ""}`),

  // Plan & Goal
  setGoal: (team: string, goal: string) => fetchApi<{ result: string }>(`/teams/${team}/goal`, { method: "POST", body: JSON.stringify({ goal }) }),
  getPlan: (team: string) => fetchApi<{ plan: { steps: string[] } }>(`/teams/${team}/plan`),
  getTaskFromTask: (team: string, description: string) => fetchApi<{ suggestions: string[] }>(`/teams/${team}/plan/recommend`, { method: "POST", body: JSON.stringify({ description }) }),

  // Negotiation
  startNegotiation: (team: string, agents: string[], resource: string) => fetchApi<{ result: string }>(`/teams/${team}/negotiate/start`, { method: "POST", body: JSON.stringify({ agents, resource }) }),
  getNegotiationStats: (team: string) => fetchApi<{ negotiations: number; resolved: number }>(`/teams/${team}/negotiate/stats`),

  // History
  getHistory: (team: string) => fetchApi<{ history: { timestamp: string; action: string }[] }>(`/teams/${team}/history`),

  // Workflows
  getWorkflows: (team: string) => fetchApi<{ workflows: Workflow[] }>(`/teams/${team}/workflows`),
  runWorkflow: (team: string, workflowId: string) => fetchApi<{ result: string }>(`/teams/${team}/workflows/${workflowId}/run`, { method: "POST" }),

  // WebSocket URL
  wsUrl: (team: string) => `${API_BASE.replace(/^http/, "ws")}/teams/${team}/ws/interactions`,

  // Hub
  getHubStatus: (team: string) => fetchApi<{ status: string; capabilities: number }>(`/teams/${team}/hub/status`),
  getHubCapabilities: (team: string) => fetchApi<{ capabilities: string[] }>(`/teams/${team}/hub/capabilities`),
  requestHelp: (team: string, task: string) => fetchApi<{ result: string }>(`/teams/${team}/hub/help`, { method: "POST", body: JSON.stringify({ task }) }),
  decomposeTask: (team: string, task: string) => fetchApi<{ subtasks: string[] }>(`/teams/${team}/hub/decompose`, { method: "POST", body: JSON.stringify({ task }) }),

  // Stats
  getTeamStats: (team: string) => fetchApi<{ total_interactions: number; by_type: Record<string, number>; unique_types: number }>(`/teams/${team}/stats`),

  // Templates
  listTemplates: () => fetchApi<{ templates: { id: string; name: string }[] }>("/templates"),
  getTemplate: (id: string) => fetchApi<{ id: string; name: string; content: string }>(`/templates/${id}`),
};