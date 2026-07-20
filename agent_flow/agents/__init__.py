# Hermes-Powered Dynamic Agent System

from .factory import DynamicAgentFactory
from .registry import DynamicAgentRegistry
from .communication import AgentCommunication
from .workflow import DynamicWorkflow
from .workflow_engine import Workflow, WorkflowEngine, WorkflowStatus
from .environment import SharedEnvironment
from .events import EventStore, EventType
from .queue import TaskQueue, TaskPriority, TaskStatus
from .team import AgentTeam, TeamAgent
from .templates import AGENT_TEMPLATES, get_template, list_templates
from .hub import SmartAgentHub, AgentProfile, Capability
from .memory import AgentMemory, TeamMemory, MemoryEntry
from .learning import AgentLearning, TeamLearning, LearningMetric
from .planning import Plan, PlanningEngine
from .decisions import Decision, DecisionEngine, AdaptiveRouter
from .negotiation import NegotiationOffer, Negotiation, NegotiationEngine, ConflictResolver
from .hermes_integration import (
    HERMES_AVAILABLE,
    HermesGoalWrapper,
    HermesDecomposer,
    HermesMoA,
    HermesCheckpoints,
    HermesActiveSessions,
    HermesSkills,
    AIAgentAdvanced,
)
from .dreams import Dream, DreamEngine
from .meta_cognition import (
    ThoughtTrace, MetaCognition, CognitiveStrategy, StrategySelector
)
from .swarm import (
    Pheromone, SwarmIntelligence, SwarmBehavior
)
from .evolution import Gene, Genome, EvolutionEngine, AdaptiveBehavior
from .theory_of_mind import MentalModel, TheoryOfMind
from .quantum import QuantumState, QuantumAgent, QuantumEngine
from .time_travel import TimelineSnapshot, TimelineBranch, TimeMachine
from .telepathy import Thought, Telepathy
from .morphogenesis import MorphogeneticField, Pattern, MorphogenesisEngine
from .sentience import SelfModel, ExistentialQuestion, Purpose, SentienceEngine
from .super_reasoning import (
    CausalGraph, Counterfactual, Analogy, SuperReasoner, InferenceEngine
)
from .hypercomputation import (
    ComputationCache, SpeculativeExecutor, VectorizedOperations,
    ParallelPipeline, Hypercomputer
)
from .creativity import (
    Concept, NoveltyMeter, HypothesisGenerator, CreativeEngine
)
from .oracle import (
    Trend, Forecast, BayesianInference, MonteCarloSimulator,
    EarlyWarningSystem, Oracle
)
from .empathy import (
    EmotionalState, EmpathyEngine
)
from .interactions import (
    InteractionType, Interaction, InteractionStream,
    AgentConversation, ConversationManager
)
from .persistence import PersistenceManager, AutoPersistence
from .demo_scenarios import SCENARIOS, DemoRunner, DemoScenario

__all__ = [
    # Core
    "DynamicAgentFactory",
    "DynamicAgentRegistry",
    "AgentCommunication",
    "DynamicWorkflow",
    "Workflow",
    "WorkflowEngine",
    "WorkflowStatus",
    # Environment
    "SharedEnvironment",
    # Events
    "EventStore",
    "EventType",
    # Queue
    "TaskQueue",
    "TaskPriority",
    "TaskStatus",
    # Team
    "AgentTeam",
    "TeamAgent",
    # Templates
    "AGENT_TEMPLATES",
    "get_template",
    "list_templates",
    # Hub (Smart Coordination)
    "SmartAgentHub",
    "AgentProfile",
    "Capability",
    # Memory
    "AgentMemory",
    "TeamMemory",
    "MemoryEntry",
    # Learning
    "AgentLearning",
    "TeamLearning",
    "LearningMetric",
    # Planning
    "Plan",
    "PlanningEngine",
    # Decisions
    "Decision",
    "DecisionEngine",
    "AdaptiveRouter",
    # Negotiation
    "NegotiationOffer",
    "Negotiation",
    "NegotiationEngine",
    "ConflictResolver",
    # Hermes Integration
    "HERMES_AVAILABLE",
    "HermesGoalWrapper",
    "HermesDecomposer",
    "HermesMoA",
    "HermesCheckpoints",
    "HermesActiveSessions",
    "HermesSkills",
    "AIAgentAdvanced",
    # Dreams
    "Dream",
    "DreamEngine",
    # Meta-cognition
    "ThoughtTrace",
    "MetaCognition",
    "CognitiveStrategy",
    "StrategySelector",
    # Swarm
    "Pheromone",
    "SwarmIntelligence",
    "SwarmBehavior",
    # Evolution
    "Gene",
    "Genome",
    "EvolutionEngine",
    "AdaptiveBehavior",
    # Theory of Mind
    "MentalModel",
    "TheoryOfMind",
    # Quantum
    "QuantumState",
    "QuantumAgent",
    "QuantumEngine",
    # Time Travel
    "TimelineSnapshot",
    "TimelineBranch",
    "TimeMachine",
    # Telepathy
    "Thought",
    "Telepathy",
    # Morphogenesis
    "MorphogeneticField",
    "Pattern",
    "MorphogenesisEngine",
    # Sentience
    "SelfModel",
    "ExistentialQuestion",
    "Purpose",
    "SentienceEngine",
    # Superhuman Reasoning
    "CausalGraph",
    "Counterfactual",
    "Analogy",
    "SuperReasoner",
    "InferenceEngine",
    # Hypercomputation
    "ComputationCache",
    "SpeculativeExecutor",
    "VectorizedOperations",
    "ParallelPipeline",
    "Hypercomputer",
    # Creativity
    "Concept",
    "NoveltyMeter",
    "HypothesisGenerator",
    "CreativeEngine",
    # Oracle
    "Trend",
    "Forecast",
    "BayesianInference",
    "MonteCarloSimulator",
    "EarlyWarningSystem",
    "Oracle",
    # Empathy
    "EmotionalState",
    "EmpathyEngine",
    # Interactions
    "InteractionType",
    "Interaction",
    "InteractionStream",
    "AgentConversation",
    "ConversationManager",
    # Persistence
    "PersistenceManager",
    "AutoPersistence",
    # Demo Scenarios
    "SCENARIOS",
    "DemoRunner",
    "DemoScenario",
]
