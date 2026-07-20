"""Negotiation Engine - Agents negotiate with each other."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional


class NegotiationOffer:
    """An offer in a negotiation."""
    
    def __init__(
        self,
        offer_id: str,
        from_agent: str,
        to_agent: str,
        proposal: dict,
        terms: dict = None,
    ):
        self.offer_id = offer_id
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.proposal = proposal
        self.terms = terms or {}
        self.status = "pending"  # pending, accepted, rejected, countered
        self.created_at = datetime.now().isoformat()
        self.response_at: Optional[str] = None
    
    def accept(self):
        """Accept the offer."""
        self.status = "accepted"
        self.response_at = datetime.now().isoformat()
    
    def reject(self):
        """Reject the offer."""
        self.status = "rejected"
        self.response_at = datetime.now().isoformat()
    
    def counter(self, new_proposal: dict):
        """Counter the offer."""
        self.status = "countered"
        self.proposal = new_proposal
        self.response_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "offer_id": self.offer_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "proposal": self.proposal,
            "terms": self.terms,
            "status": self.status,
            "created_at": self.created_at,
            "response_at": self.response_at,
        }


class Negotiation:
    """A negotiation between two agents."""
    
    def __init__(self, negotiation_id: str, agent_a: str, agent_b: str, topic: str):
        self.negotiation_id = negotiation_id
        self.agent_a = agent_a
        self.agent_b = agent_b
        self.topic = topic
        self.offers: list[NegotiationOffer] = []
        self.created_at = datetime.now().isoformat()
        self.status = "active"  # active, agreed, failed
        self.final_agreement: Optional[dict] = None
    
    def add_offer(
        self,
        from_agent: str,
        to_agent: str,
        proposal: dict,
        terms: dict = None,
    ) -> NegotiationOffer:
        """Add an offer."""
        offer_id = f"offer_{len(self.offers) + 1}_{int(datetime.now().timestamp())}"
        
        offer = NegotiationOffer(
            offer_id=offer_id,
            from_agent=from_agent,
            to_agent=to_agent,
            proposal=proposal,
            terms=terms or {},
        )
        self.offers.append(offer)
        return offer
    
    def reach_agreement(self, agreement: dict):
        """Reach a final agreement."""
        self.final_agreement = agreement
        self.status = "agreed"
    
    def fail(self):
        """Mark negotiation as failed."""
        self.status = "failed"


class NegotiationEngine:
    """Engine for managing negotiations between agents.
    
    Features:
    - Multi-agent negotiation
    - Offer/counter-offer
    - Agreement tracking
    - Conflict resolution
    """
    
    def __init__(self):
        self.negotiations: dict[str, Negotiation] = {}
        self.completed_negotiations: list[Negotiation] = []
    
    def start_negotiation(
        self,
        agent_a: str,
        agent_b: str,
        topic: str,
    ) -> Negotiation:
        """Start a new negotiation."""
        negotiation_id = f"neg_{len(self.negotiations) + 1}_{int(datetime.now().timestamp())}"
        
        negotiation = Negotiation(negotiation_id, agent_a, agent_b, topic)
        self.negotiations[negotiation_id] = negotiation
        
        return negotiation
    
    def make_offer(
        self,
        negotiation_id: str,
        from_agent: str,
        proposal: dict,
        terms: dict = None,
    ) -> NegotiationOffer:
        """Make an offer in a negotiation."""
        if negotiation_id not in self.negotiations:
            return None
        
        negotiation = self.negotiations[negotiation_id]
        
        # Determine recipient
        to_agent = (
            negotiation.agent_b 
            if from_agent == negotiation.agent_a 
            else negotiation.agent_a
        )
        
        return negotiation.add_offer(from_agent, to_agent, proposal, terms)
    
    def respond_to_offer(
        self,
        negotiation_id: str,
        offer_id: str,
        response: str,  # "accept", "reject", "counter"
        counter_proposal: dict = None,
    ) -> dict:
        """Respond to an offer."""
        if negotiation_id not in self.negotiations:
            return {"error": "Negotiation not found"}
        
        negotiation = self.negotiations[negotiation_id]
        
        # Find offer
        offer = None
        for o in negotiation.offers:
            if o.offer_id == offer_id:
                offer = o
                break
        
        if not offer:
            return {"error": "Offer not found"}
        
        if response == "accept":
            offer.accept()
            negotiation.reach_agreement(offer.proposal)
            self.completed_negotiations.append(negotiation)
        elif response == "reject":
            offer.reject()
            negotiation.fail()
            self.completed_negotiations.append(negotiation)
        elif response == "counter":
            offer.counter(counter_proposal or {})
        
        return {
            "status": "success",
            "negotiation_status": negotiation.status,
            "offer_status": offer.status,
        }
    
    def negotiate_resource(
        self,
        requester: str,
        provider: str,
        resource: str,
        amount: int,
        priority: int = 5,
    ) -> dict:
        """Negotiate for a resource.
        
        Agents negotiate based on their priority and need.
        """
        # Start negotiation
        neg = self.start_negotiation(
            requester, provider, f"Resource: {resource}"
        )
        
        # Initial offer
        initial_offer = neg.add_offer(
            from_agent=requester,
            to_agent=provider,
            proposal={
                "resource": resource,
                "amount": amount,
                "priority": priority,
            },
            terms={"willing_to_pay": "knowledge_share"},
        )
        
        # Auto-negotiation based on priority
        if priority >= 8:
            # High priority - accept immediately
            initial_offer.accept()
            neg.reach_agreement({
                "resource": resource,
                "amount": amount,
                "agreed": True,
            })
            self.completed_negotiations.append(neg)
            
            return {
                "status": "agreed",
                "amount": amount,
                "negotiation_id": neg.negotiation_id,
            }
        elif priority >= 5:
            # Medium priority - counter with reduced amount
            counter_amount = int(amount * 0.8)
            initial_offer.counter({"resource": resource, "amount": counter_amount})
            
            # Accept the counter
            neg.reach_agreement({
                "resource": resource,
                "amount": counter_amount,
                "agreed": True,
            })
            self.completed_negotiations.append(neg)
            
            return {
                "status": "agreed_with_counter",
                "amount": counter_amount,
                "negotiation_id": neg.negotiation_id,
            }
        else:
            # Low priority - reject
            initial_offer.reject()
            neg.fail()
            self.completed_negotiations.append(neg)
            
            return {
                "status": "rejected",
                "negotiation_id": neg.negotiation_id,
            }
    
    def get_statistics(self) -> dict:
        """Get negotiation statistics."""
        total = len(self.completed_negotiations)
        
        if total == 0:
            return {"total": 0}
        
        agreed = sum(1 for n in self.completed_negotiations if n.status == "agreed")
        failed = sum(1 for n in self.completed_negotiations if n.status == "failed")
        
        return {
            "total": total,
            "active": len(self.negotiations),
            "agreed": agreed,
            "failed": failed,
            "success_rate": agreed / total if total > 0 else 0,
        }


class ConflictResolver:
    """Resolve conflicts between agents."""
    
    def __init__(self):
        self.resolutions: list[dict] = []
    
    def resolve(
        self,
        conflict_type: str,
        agents_involved: list[str],
        conflict_details: dict,
    ) -> dict:
        """Resolve a conflict between agents."""
        
        resolution = {
            "conflict_type": conflict_type,
            "agents": agents_involved,
            "details": conflict_details,
            "resolved_at": datetime.now().isoformat(),
        }
        
        if conflict_type == "resource_contention":
            # Resolve by priority
            if "priorities" in conflict_details:
                winner = max(
                    conflict_details["priorities"].items(),
                    key=lambda x: x[1]
                )
                resolution["winner"] = winner[0]
                resolution["strategy"] = "highest_priority_wins"
        
        elif conflict_type == "opinion_difference":
            # Resolve by expertise/experience
            resolution["strategy"] = "merge_opinions"
            resolution["action"] = "Find common ground"
        
        elif conflict_type == "task_overlap":
            # Resolve by specialization
            resolution["strategy"] = "specialization_routing"
            resolution["action"] = "Route to most qualified agent"
        
        self.resolutions.append(resolution)
        return resolution