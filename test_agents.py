#!/usr/bin/env python3
"""Test script for multi-agent system"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
env_file = PROJECT_ROOT / '.env'
if env_file.exists():
    print(f"Loading environment variables from {env_file}")
    load_dotenv(env_file)
else:
    print("Warning: .env file not found!")

# Initialize skills
from src.skills.skill_initializer import initialize_skills
initialize_skills()

from src.graph.workflow import create_workflow, WorkflowState, format_workflow_result


def test_workflow():
    """Test the complete workflow"""
    print("Testing Multi-Agent Programming Assistant System")
    print("=" * 50)

    # Create workflow
    workflow = create_workflow(max_iterations=3)

    # Test state
    test_state = WorkflowState(
        task_description="写一个冒泡排序",
        session_id="test-session-001",
        task_plan=None,
        repo_analysis=None,
        generated_code=None,
        review_result=None,
        fixed_code=None,
        workflow_steps=[],
        error=None,
        progress_callback=None,
        iteration_count=0,
        max_iterations=3
    )

    # Run workflow
    print("\n🚀 Starting workflow...")
    print(f"\n📝 Task: {test_state['task_description']}")

    try:
        # Execute the entire workflow in one go
        print("\n🔄 Executing full workflow...")
        result = workflow.invoke(test_state)

        print("\n" + "=" * 50)
        print("WORKFLOW EXECUTION COMPLETED!")
        print("=" * 50)

        # Check for errors
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
            return False

        # Format and display results
        final_result = format_workflow_result(result)

        print(f"\n📝 Task: {final_result['task_description']}")
        print(f"📊 Iterations: {final_result['iterations']}")
        print(f"📋 Plan: {final_result['task_plan']['task'] if final_result['task_plan'] else 'N/A'}")

        if final_result['repo_analysis']:
            main_files = final_result['repo_analysis'].get('main_files', [])
            print(f"🔍 Found {len(main_files)} relevant files")
            if main_files:
                print("   - " + "\n   - ".join(main_files[:3]))

        if final_result['final_code']:
            print(f"💻 Final code length: {len(final_result['final_code'])} characters")

        if final_result['review_result']:
            print(f"🔍 Review score: {final_result['review_result'].get('score', 'N/A')}/10")
            print(f"🔍 Review status: {'Needs revision' if final_result['review_result'].get('needs_revision') else 'Passed'}")

        if final_result['test_result']:
            test_analysis = final_result['test_result'].get('analysis', {})
            print(f"🧪 Test status: {test_analysis.get('status', 'N/A')}")
            if test_analysis.get('status') == 'success':
                print(f"🧪 All tests passed!")

        # Show workflow steps
        print(f"\n📋 Workflow steps completed: {len(final_result['workflow_steps'])}")
        for step in final_result['workflow_steps']:
            status_icon = "✅" if step['status'] == 'completed' else "❌"
            print(f"   {status_icon} {step['description']}")

        # Show generated code
        print("\n📄 Generated Code:")
        print("-" * 40)
        code = final_result['final_code']
        if len(code) > 500:
            print(code[:500] + "\n...")
        else:
            print(code)
        print("-" * 40)

        return True

    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_skills():
    """Test individual skills"""
    print("\n" + "=" * 50)
    print("TESTING INDIVIDUAL SKILLS")
    print("=" * 50)

    from src.skills.skill_registry import skill_registry

    # List all skills
    print("\n📋 Registered Skills:")
    for skill_info in skill_registry.list_skills():
        print(f"  - {skill_info['name']}: {skill_info['type']}")

    # Test file search skill
    print("\n🔍 Testing File Search Skill...")
    try:
        from src.skills.file_search_skill import FileSearchSkill
        file_search = FileSearchSkill()
        result = file_search.execute("test", ".")
        print(f"  Result: Found {result.get('total', 0)} files matching 'test'")
    except Exception as e:
        print(f"  Error: {str(e)}")

    # Test model router skill
    print("\n🚀 Testing Model Router Skill...")
    try:
        from src.skills.model_router import ModelRouterSkill
        model_router = ModelRouterSkill()
        result = model_router.execute("implementer", "simple coding task", "low")
        print(f"  Selected model: {result.get('selected_model', 'N/A')}")
        print(f"  Reasoning: {result.get('reasoning', 'N/A')}")
    except Exception as e:
        print(f"  Error: {str(e)}")


if __name__ == "__main__":
    # Test skills first
    test_skills()

    # Test full workflow
    success = test_workflow()

    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)