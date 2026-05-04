"""Base agent class with skill integration"""

from typing import Dict, Any, List, Optional
from src.skills.skill_registry import skill_registry, BaseSkill
from src.llm.llm_model_client import get_agent_llm_client


class BaseAgent:
    """Base class for all agents with skill support"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.client = get_agent_llm_client(agent_name)
        self.skills = skill_registry.get_skills_for_agent(agent_name)

    def use_skill(self, skill_name: str, *args, **kwargs) -> Any:
        """Use a skill available to this agent"""
        skill = skill_registry.get_skill(skill_name)
        if skill:
            return skill.execute(*args, **kwargs)
        else:
            raise ValueError(f"Skill '{skill_name}' not available for agent '{self.agent_name}'")

    def get_available_skills(self) -> List[Dict[str, Any]]:
        """Get list of available skills for this agent"""
        return [
            {
                "name": skill.metadata.name,
                "description": skill.metadata.description,
                "type": skill.metadata.skill_type.value,
                "risk_level": skill.metadata.risk_level.value,
                "stats": skill.get_execution_stats()
            }
            for skill in self.skills
        ]

    def format_skills_context(self) -> str:
        """Format skills information for LLM context"""
        if not self.skills:
            return ""

        skills_info = "Available skills:\n"
        for skill in self.skills:
            skills_info += f"- {skill.metadata.name}: {skill.metadata.description}\n"

        return skills_info