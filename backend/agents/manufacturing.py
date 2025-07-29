"""Manufacturing Agent for UAV design system using LangGraph create_react_agent."""

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
from pydantic_models import ManufacturingOutput
from prompts import MANUFACTURING_SYSTEM


class ManufacturingAgent(BaseAgent):
    """Manufacturing Agent - analyzes manufacturability and costs."""
    
    def __init__(self, llm: ChatOpenAI, tools: List):
        super().__init__("manufacturing", llm, tools, ManufacturingOutput, MANUFACTURING_SYSTEM)
    
    def check_dependencies_ready(self, state: StaticGlobalState) -> bool:
        """Needs output from structures agent."""
        return len(state.structures_outputs) > 0
    
    def get_dependency_outputs(self, state: StaticGlobalState) -> Dict[str, Any]:
        """Get latest structures output."""
        if state.structures_outputs:
            latest_key = max(state.structures_outputs.keys())
            return {
                "structures": state.structures_outputs[latest_key]
            }
        return {}