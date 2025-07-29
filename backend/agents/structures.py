"""Structures Agent for UAV design system using LangGraph create_react_agent."""

from typing import Dict, List, Any
from langchain_openai import ChatOpenAI

import sys
import os
<<<<<<< HEAD
# Add parent directory to path to import backend modules
current_dir = os.path.dirname(__file__)
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)
=======
from pathlib import Path

# Add parent directory to path to import backend modules using pathlib
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
sys.path.insert(0, str(backend_dir))
>>>>>>> ae778f3 (second commit)
from agents.base_agent import BaseAgent
from langgraph.state import StaticGlobalState
from pydantic_models import StructuresOutput
from prompts import STRUCTURES_SYSTEM


class StructuresAgent(BaseAgent):
    """Structures Agent - designs structural components."""
    
    def __init__(self, llm: ChatOpenAI, tools: List):
        super().__init__("structures", llm, tools, StructuresOutput, STRUCTURES_SYSTEM)
    
    def check_dependencies_ready(self, state: StaticGlobalState) -> bool:
        """Needs MTOW from mission planner and wing geometry from aerodynamics."""
        return (len(state.mission_planner_outputs) > 0 and 
                len(state.aerodynamics_outputs) > 0)
    
    def _debug_dependency_status(self, state: StaticGlobalState):
        """Debug what dependencies are missing."""
        print(f"     Mission planner outputs: {len(state.mission_planner_outputs)} available")
        print(f"     Aerodynamics outputs: {len(state.aerodynamics_outputs)} available")
    
    def get_dependency_outputs(self, state: StaticGlobalState) -> Dict[str, Any]:
        """Get latest mission planner and aerodynamics outputs."""
        result = {}
        if state.mission_planner_outputs:
            latest_key = max(state.mission_planner_outputs.keys())
            result["mission_plan"] = state.mission_planner_outputs[latest_key]
        if state.aerodynamics_outputs:
            latest_key = max(state.aerodynamics_outputs.keys())
            result["aerodynamics"] = state.aerodynamics_outputs[latest_key]
        return result