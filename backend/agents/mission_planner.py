"""Mission Planner Agent for UAV design system using LangGraph create_react_agent."""

from typing import Dict, List, Any
from langchain_openai import ChatOpenAI

import sys
import os
from pathlib import Path

# Add parent directory to path to import backend modules using pathlib
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
sys.path.insert(0, str(backend_dir))

from agents.base_agent import BaseAgent
from langgraph.state import StaticGlobalState
from pydantic_models import MissionPlannerOutput
from prompts import MISSION_PLANNER_SYSTEM


class MissionPlannerAgent(BaseAgent):
    """Mission Planner Agent - defines mission requirements and MTOW."""
    
    def __init__(self, llm: ChatOpenAI, tools: List):
        super().__init__("mission_planner", llm, tools, MissionPlannerOutput, MISSION_PLANNER_SYSTEM)
    
    def check_dependencies_ready(self, state: StaticGlobalState) -> bool:
        """Mission planner has no dependencies."""
        return True
    
    def get_dependency_outputs(self, state: StaticGlobalState) -> Dict[str, Any]:
        """Mission planner has no dependencies."""
        return {}