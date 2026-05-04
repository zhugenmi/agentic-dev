"""Skill registry for managing available skills"""

from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import json
import time
from dataclasses import dataclass
from abc import ABC, abstractmethod


class SkillType(Enum):
    """Types of skills"""
    PROMPT = "prompt"
    TOOL = "tool"
    RESOURCE = "resource"


class SkillRiskLevel(Enum):
    """Risk levels for skills"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class SkillMetadata:
    """Metadata for a skill"""
    name: str
    description: str
    skill_type: SkillType
    risk_level: SkillRiskLevel
    version: str = "1.0.0"
    author: str = "system"
    tags: List[str] = None
    cost_estimate: Optional[float] = None
    execution_timeout: Optional[int] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class BaseSkill(ABC):
    """Base class for all skills"""

    def __init__(self, metadata: SkillMetadata):
        self.metadata = metadata
        self.execution_history: List[Dict[str, Any]] = []

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the skill"""
        pass

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for h in self.execution_history if h.get("success", False))
        avg_duration = sum(h.get("duration", 0) for h in self.execution_history) / max(total_executions, 1)

        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / max(total_executions, 1),
            "average_duration": avg_duration,
            "last_execution": self.execution_history[-1] if self.execution_history else None
        }

    def record_execution(self, success: bool, duration: float, result: Any = None, error: str = None):
        """Record execution history"""
        self.execution_history.append({
            "timestamp": time.time(),
            "success": success,
            "duration": duration,
            "result": result,
            "error": error
        })


class SkillRegistry:
    """Registry for managing skills"""

    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self.agent_permissions: Dict[str, List[str]] = {}

    def register_skill(self, skill: BaseSkill, allowed_agents: List[str] = None):
        """Register a skill"""
        self.skills[skill.metadata.name] = skill
        if allowed_agents:
            self.agent_permissions[skill.metadata.name] = allowed_agents

    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """Get a skill by name"""
        return self.skills.get(name)

    def get_skills_for_agent(self, agent_name: str) -> List[BaseSkill]:
        """Get all skills available to an agent"""
        available_skills = []
        for skill_name, agents in self.agent_permissions.items():
            if agent_name in agents:
                skill = self.skills.get(skill_name)
                if skill:
                    available_skills.append(skill)
        return available_skills

    def list_skills(self) -> List[Dict[str, Any]]:
        """List all skills with metadata"""
        return [
            {
                "name": skill.metadata.name,
                "description": skill.metadata.description,
                "type": skill.metadata.skill_type.value,
                "risk_level": skill.metadata.risk_level.value,
                "version": skill.metadata.version,
                "tags": skill.metadata.tags,
                "stats": skill.get_execution_stats()
            }
            for skill in self.skills.values()
        ]

    def unregister_skill(self, name: str):
        """Unregister a skill"""
        if name in self.skills:
            del self.skills[name]
        if name in self.agent_permissions:
            del self.agent_permissions[name]


# Global skill registry instance
skill_registry = SkillRegistry()