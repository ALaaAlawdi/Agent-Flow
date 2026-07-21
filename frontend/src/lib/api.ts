const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export type Team = {
  name: string;
  goal: string;
  created_at: string;
};

export type Interaction = {
  interaction_id: string;
  type: string;
  source: string | null;
  target: string | null;
  data: Record<string, unknown>;
  summary: string;
  timestamp: string;
};

export type InteractionStats = {
  total_interactions: number;
  unique_types: number;
  unique_agents: number;
  by_type: Record<string, number>;
  by_agent: Record<string, number>;
};

export type Scenario = {
  scenario_id: string;
  title: string;
  description: string;
  icon: string;
  category: string;
  team_size: number;
  step_count: number;
  estimated_time: string;
};

export type ScenarioResult = {
  scenario_id: string;
  title: string;
  team_name: string;
  agents_added: string[];
  steps_executed: number;
  successful_steps: number;
  stats: {
    interactions: { total_interactions: number; unique_types: number };
    active_agents: { agent_id: string; interactions: number }[];
  };
};

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export const api = {
  // Health
  health: () => fetchApi<{ status: string }>("/health"),

  // Scenarios
  listScenarios: () => fetchApi<{ scenarios: Scenario[] }>("/scenarios"),
  getScenario: (id: string) => fetchApi<Scenario & { team_config: Record<string, unknown> }>(`/scenarios/${id}`),
  runScenario: (id: string) =>
    fetchApi<ScenarioResult>(`/scenarios/${id}/run`, { method: "POST" }),

  // Teams
  listTeams: () => fetchApi<{ teams: Team[] }>("/teams"),
  getTeamStats: (name: string) => fetchApi<{ total_interactions: number; by_type: Record<string, number> }>(`/teams/${name}/interactions/stats`),
  getInteractions: (name: string, limit = 50) =>
    fetchApi<{ interactions: Interaction[] }>(`/teams/${name}/interactions?limit=${limit}`),
  getActiveAgents: (name: string) =>
    fetchApi<{ active_agents: { agent_id: string; interactions: number }[] }>(`/teams/${name}/interactions/active-agents`),
  getInteractionGraph: (name: string) =>
    fetchApi<{ nodes: { id: string }[]; edges: { source: string; target: string; weight: number }[] }>(`/teams/${name}/interactions/graph`),

  // Models
  listModels: () => fetchApi<{ models: { short_name: string; provider: string }[] }>("/models"),
};