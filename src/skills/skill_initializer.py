"""Initialize and register all skills"""

from .skill_registry import skill_registry
from .file_search_skill import FileSearchSkill
from .code_analysis_skill import CodeAnalysisSkill
from .model_router import ModelRouterSkill
from .file_operations_skill import FileOperationsSkill, DirectoryOperationsSkill
from .project_scaffold_skill import ProjectScaffoldSkill


def initialize_skills():
    """Initialize and register all skills"""
    # Register file search skill
    file_search_skill = FileSearchSkill()
    skill_registry.register_skill(
        file_search_skill,
        allowed_agents=["repo_analyst", "implementer", "supervisor"]
    )

    # Register code analysis skill
    code_analysis_skill = CodeAnalysisSkill()
    skill_registry.register_skill(
        code_analysis_skill,
        allowed_agents=["repo_analyst", "reviewer", "implementer"]
    )

    # Register model router skill
    model_router_skill = ModelRouterSkill()
    skill_registry.register_skill(
        model_router_skill,
        allowed_agents=["supervisor", "repo_analyst", "implementer", "reviewer", "tester"]
    )

    # Register file operations skill
    file_ops_skill = FileOperationsSkill()
    skill_registry.register_skill(
        file_ops_skill,
        allowed_agents=["implementer", "repo_analyst"]
    )

    # Register directory operations skill
    dir_ops_skill = DirectoryOperationsSkill()
    skill_registry.register_skill(
        dir_ops_skill,
        allowed_agents=["implementer", "repo_analyst"]
    )

    # Register project scaffold skill
    scaffold_skill = ProjectScaffoldSkill()
    skill_registry.register_skill(
        scaffold_skill,
        allowed_agents=["repo_analyst", "implementer"]
    )

    print("Skills registered successfully!")
    print(f"Total skills: {len(skill_registry.skills)}")

    # Print skill list
    for skill_info in skill_registry.list_skills():
        print(f"- {skill_info['name']}: {skill_info['description']} ({skill_info['type']})")


def get_skills_for_agent(agent_name: str):
    """Get all skills available for a specific agent"""
    return skill_registry.get_skills_for_agent(agent_name)