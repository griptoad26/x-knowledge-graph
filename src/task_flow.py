"""
Task Flow Manager for knowledge graph.
Handles action completion, dependencies, and next-action progression.
"""

from typing import Dict, List, Any, Optional, Set
from collections import deque
from dataclasses import dataclass, field


@dataclass
class TaskFlow:
    """Represents a flow of related tasks"""
    topic: str
    actions: List[Dict] = field(default_factory=list)
    current_action_index: int = 0
    status: str = "pending"  # pending, in_progress, completed, blocked
    
    def to_dict(self) -> Dict:
        return {
            "topic": self.topic,
            "actions": self.actions,
            "current_action_index": self.current_action_index,
            "status": self.status
        }


class TaskFlowManager:
    """
    Manages task flows with dependency resolution and progression.
    
    Features:
    - Build flows from action graph
    - Track completion status
    - Auto-suggest next action
    - Handle dependencies between actions
    """
    
    def __init__(self):
        self.flows: Dict[str, TaskFlow] = {}
    
    def build_flows(self, graph) -> Dict[str, TaskFlow]:
        """
        Build task flows from graph actions grouped by topic.
        
        Returns dict of topic -> TaskFlow
        """
        # Get pending actions grouped by topic
        actions_by_topic = graph.get_actions_by_topic()
        
        self.flows = {}
        
        for topic, actions in actions_by_topic.items():
            # Sort actions within topic
            sorted_actions = self._sort_actions(actions)
            
            flow = TaskFlow(
                topic=topic,
                actions=sorted_actions,
                current_action_index=0,
                status="in_progress" if sorted_actions else "completed"
            )
            
            self.flows[topic] = flow
        
        return {k: v.to_dict() for k, v in self.flows.items()}
    
    def _sort_actions(self, actions: List[Dict]) -> List[Dict]:
        """Sort actions by priority and dependency"""
        if not actions:
            return []
        
        # Sort by priority (urgent -> high -> medium -> low)
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        
        sorted_actions = sorted(
            actions,
            key=lambda x: (
                priority_order.get(x.get("priority"), 4),
                -x.get("confidence", 0)
            )
        )
        
        return sorted_actions
    
    def get_next_action(self, graph, topic: Optional[str] = None) -> Optional[Dict]:
        """
        Get the next action to complete.
        
        If topic specified, return next in that topic.
        Otherwise, return highest priority next action across topics.
        """
        if topic:
            flow = self.flows.get(topic)
            if not flow:
                return None
            
            # Get current action in flow
            if flow.current_action_index < len(flow.actions):
                return flow.actions[flow.current_action_index]
            return None
        
        # Find highest priority next action across all topics
        next_actions = []
        
        for topic, flow in self.flows.items():
            if flow.status == "in_progress" and flow.current_action_index < len(flow.actions):
                action = flow.actions[flow.current_action_index]
                action["topic"] = topic
                next_actions.append(action)
        
        if not next_actions:
            return None
        
        # Return highest priority
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        next_actions.sort(key=lambda x: priority_order.get(x.get("priority"), 4))
        
        return next_actions[0]
    
    def complete_action(self, graph, action_id: str) -> Optional[Dict]:
        """
        Mark an action as complete and return the next action in the flow.
        """
        # Find which flow this action belongs to
        for topic, flow in self.flows.items():
            for i, action in enumerate(flow.actions):
                if action.get("id") == action_id:
                    # Mark in graph
                    graph.mark_action_complete(action_id)
                    
                    # Advance flow
                    flow.current_action_index = i + 1
                    
                    # Check if flow is complete
                    if flow.current_action_index >= len(flow.actions):
                        flow.status = "completed"
                    
                    # Return next action
                    return self.get_next_action(graph, topic)
        
        return None
    
    def complete_action_by_text(self, graph, text: str) -> Optional[Dict]:
        """Complete an action by matching text (fuzzy match)"""
        pending_actions = graph.get_pending_actions()
        
        for action in pending_actions:
            if text.lower() in action.get("text", "").lower():
                return self.complete_action(graph, action["id"])
        
        return None
    
    def get_flow_status(self, topic: str) -> Optional[Dict]:
        """Get detailed status of a task flow"""
        flow = self.flows.get(topic)
        if not flow:
            return None
        
        total = len(flow.actions)
        completed = flow.current_action_index
        pending = total - completed
        
        return {
            "topic": topic,
            "status": flow.status,
            "total_actions": total,
            "completed_actions": completed,
            "pending_actions": pending,
            "progress_percent": (completed / total * 100) if total > 0 else 100,
            "current_action": flow.actions[completed] if completed < total else None,
            "next_action": self._get_next_in_flow(flow),
            "is_blocked": self._is_flow_blocked(flow)
        }
    
    def _get_next_in_flow(self, flow: TaskFlow) -> Optional[Dict]:
        """Get next action in a specific flow"""
        if flow.current_action_index < len(flow.actions):
            action = flow.actions[flow.current_action_index].copy()
            action["step"] = flow.current_action_index + 1
            action["total_steps"] = len(flow.actions)
            return action
        return None
    
    def _is_flow_blocked(self, flow: TaskFlow) -> bool:
        """Check if flow is blocked by unmet dependencies"""
        if flow.current_action_index >= len(flow.actions):
            return False
        
        current_action = flow.actions[flow.current_action_index]
        
        # In production, check actual graph dependencies
        # For now, assume no blocking
        return False
    
    def get_all_flows_summary(self) -> List[Dict]:
        """Get summary of all task flows"""
        summaries = []
        
        for topic in self.flows:
            summaries.append(self.get_flow_status(topic))
        
        # Sort by progress (most complete first)
        summaries.sort(key=lambda x: x["progress_percent"] if x else 0, reverse=True)
        
        return summaries
    
    def get_actionable_topics(self) -> List[str]:
        """Get list of topics with pending actions"""
        return [
            topic for topic, flow in self.flows.items()
            if flow.status == "in_progress" and flow.current_action_index < len(flow.actions)
        ]
    
    def suggest_focus(self, graph) -> Dict[str, Any]:
        """
        Suggest what to focus on next based on urgency and dependencies.
        """
        next_action = self.get_next_action(graph)
        
        if not next_action:
            return {
                "message": "All actions complete! 🎉",
                "actions_remaining": 0,
                "next_action": None
            }
        
        priority = next_action.get("priority", "medium")
        topic = next_action.get("topic", "uncategorized")
        
        suggestions = {
            "message": f"Next: {next_action['text'][:100]}...",
            "priority": priority,
            "topic": topic,
            "confidence": next_action.get("confidence", 0.5),
            "actions_remaining": len(graph.get_pending_actions()),
            "next_action": next_action
        }
        
        # Add urgency note if urgent
        if priority == "urgent":
            suggestions["note"] = "⚠️ This is marked as urgent!"
        
        return suggestions
    
    def build_dependency_graph(self, graph) -> Dict[str, Set[str]]:
        """
        Build dependency map from graph actions.
        Returns dict: action_id -> set of prerequisite action_ids
        """
        dependencies = {}
        
        for node_id, data in graph.graph.nodes(data=True):
            if data.get("type") == "action":
                deps = set()
                
                # Check predecessors for action nodes
                for pred in graph.graph.predecessors(node_id):
                    if graph.graph.nodes[pred].get("type") == "action":
                        deps.add(pred)
                
                dependencies[node_id] = deps
        
        return dependencies
    
    def can_complete(self, action_id: str, dependencies: Dict[str, Set[str]]) -> bool:
        """Check if an action can be completed (all deps complete)"""
        deps = dependencies.get(action_id, set())
        return len(deps) == 0
