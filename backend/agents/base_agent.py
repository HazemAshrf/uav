"""Base agent class for all UAV design agents using LangGraph's create_react_agent."""

import asyncio
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
import functools

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

from langgraph.state import StaticGlobalState
from pydantic_models import AgentMessage
from prompts import (
    format_agent_system_message,
    format_agent_human_message_with_context
)
from config import COMMUNICATION_RULES


class BaseAgent:
    """Base class for all UAV design agents using LangGraph's create_react_agent."""
    
    def __init__(self, name: str, llm: ChatOpenAI, tools: List, output_class, system_prompt: str):
        self.name = name
        self.llm = llm
        self.tools = tools
        self.output_class = output_class
        self.system_prompt = system_prompt
        self.communication_allowed = COMMUNICATION_RULES.get(self.name, [])
    
    def can_communicate_with(self, other_agent: str) -> bool:
        """Check if this agent can communicate with another agent."""
        return other_agent in self.communication_allowed
    
    def get_task_for_current_iteration(self, state: StaticGlobalState) -> Optional[str]:
        """Get task from coordinator chat messages for current iteration or most recent iteration with tasks."""
        # Get chat with coordinator
        coordinator_chat = state.get_chat("coordinator", self.name)
        if not coordinator_chat:
            return None
        
        # First try current iteration
        current_messages = coordinator_chat.get_messages_for_iteration(state.current_iteration)
        for msg in current_messages:
            if msg.from_agent == "coordinator" and msg.to_agent == self.name:
                if msg.message_type == "task_assignment":
                    return msg.content
        
        # If no task in current iteration, find most recent iteration with tasks
        for iteration in range(state.current_iteration - 1, -1, -1):
            iteration_messages = coordinator_chat.get_messages_for_iteration(iteration)
            for msg in iteration_messages:
                if msg.from_agent == "coordinator" and msg.to_agent == self.name:
                    if msg.message_type == "task_assignment":
                        return msg.content
        
        return None
    
    def get_messages_from_previous_iteration(self, state: StaticGlobalState) -> List[Dict[str, str]]:
        """Get messages from previous iteration only."""
        if state.current_iteration <= 0:
            return []
        
        prev_iteration = state.current_iteration - 1
        messages = state.get_messages_for_agent(self.name, prev_iteration)
        return [{"from": msg.from_agent, "content": msg.content} for msg in messages]
    
    def get_own_previous_output(self, state: StaticGlobalState) -> Dict[str, Any]:
        """Get this agent's most recent previous output."""
        outputs_dict = getattr(state, f"{self.name}_outputs")
        if not outputs_dict:
            return {}
        
        latest_key = max(outputs_dict.keys())
        return {"previous_output": outputs_dict[latest_key]}
    
    def get_communicable_agents_outputs(self, state: StaticGlobalState) -> Dict[str, Any]:
        """Get latest outputs from agents this agent can communicate with."""
        communicable_outputs = {}
        
        for agent_name in self.communication_allowed:
            outputs_dict = getattr(state, f"{agent_name}_outputs")
            if outputs_dict:
                latest_key = max(outputs_dict.keys())
                communicable_outputs[agent_name] = outputs_dict[latest_key]
        
        return communicable_outputs
    
    def get_complete_agent_history(self, state: StaticGlobalState) -> List[Dict[str, Any]]:
        """Get complete history of messages sent and received by this agent using chat system."""
        history = []
        
        for iteration in range(state.current_iteration):
            received_messages = []
            sent_messages = []
            
            # Get messages from all chats involving this agent
            for chat in state.chats.values():
                if self.name in chat.participants:
                    iteration_messages = chat.get_messages_for_iteration(iteration)
                    
                    for msg in iteration_messages:
                        if msg.to_agent == self.name:
                            received_messages.append({"from": msg.from_agent, "content": msg.content})
                        elif msg.from_agent == self.name:
                            sent_messages.append({"to": msg.to_agent, "content": msg.content})
            
            if received_messages or sent_messages:
                history.append({
                    "iteration": iteration,
                    "received": received_messages,
                    "sent": sent_messages
                })
        
        return history
    
    def check_dependencies_ready(self, state: StaticGlobalState) -> bool:
        """Check if required agent outputs exist."""
        return True  # Override in subclasses
    
    def get_dependency_outputs(self, state: StaticGlobalState) -> Dict[str, Any]:
        """Get outputs from dependent agents."""
        return {}  # Override in subclasses
    
    def debug_dependencies(self, state: StaticGlobalState):
        """Debug dependency status."""
        deps_ready = self.check_dependencies_ready(state)
        if not deps_ready:
            print(f"⚠️  {self.name}: Dependencies not ready for iteration {state.current_iteration}")
            # Show what dependencies are missing
            if hasattr(self, '_debug_dependency_status'):
                self._debug_dependency_status(state)
    
    def should_update_last_iteration(self, state: StaticGlobalState, new_output) -> bool:
        """Determine if this output represents an update (vs maintaining current values)."""
        current_iter = state.current_iteration
        outputs_dict = getattr(state, f"{self.name}_outputs")
        
        # If this is the first output, it's always an update
        if not outputs_dict:
            return True
        
        # Get the most recent previous output
        previous_keys = [k for k in outputs_dict.keys() if k < current_iter]
        if not previous_keys:
            return True
        
        latest_previous_key = max(previous_keys)
        previous_output = outputs_dict[latest_previous_key]
        
        # Compare key parameters to determine if this is an update
        if hasattr(new_output, 'dict') and hasattr(previous_output, 'dict'):
            new_dict = new_output.dict()
            prev_dict = previous_output.dict()
            
            # Remove metadata fields for comparison
            for field in ['iteration', 'messages']:
                new_dict.pop(field, None)
                prev_dict.pop(field, None)
            
            # If the core parameters are different, it's an update
            return new_dict != prev_dict
        
        return True
    
    def send_messages(self, state: StaticGlobalState, messages: List[AgentMessage]):
        """Send messages to other agents using chat system."""
        for msg in messages:
            if self.can_communicate_with(msg.to_agent):
                state.send_message(
                    from_agent=self.name,
                    to_agent=msg.to_agent,
                    content=msg.content,
                    message_type="communication",
                    metadata={"iteration": state.current_iteration}
                )
            else:
                print(f"⚠️  Warning: {self.name} cannot send message to '{msg.to_agent}'")
    
    def create_agent_pre_model_hook(self, state: StaticGlobalState):
        """Create pre_model_hook for this agent with current state context."""
        def pre_model_hook(agent_state, config):
            # Get current context
            current_iter = state.current_iteration
            task = self.get_task_for_current_iteration(state)
            dependencies = self.get_dependency_outputs(state)
            messages_received = self.get_messages_from_previous_iteration(state)
            history = self.get_complete_agent_history(state)
            
            # Get own previous output and communicable agents' outputs
            own_previous = self.get_own_previous_output(state)
            communicable_outputs = self.get_communicable_agents_outputs(state)
            
            # Create messages for LLM
            messages = []
            
            # System message with agent role and instructions
            system_content = format_agent_system_message(
                self.system_prompt,
                self.tools,
                current_iter
            )
            messages.append(SystemMessage(content=system_content))
            
            # Human message with complete context
            human_content = format_agent_human_message_with_context(
                task,
                dependencies,
                messages_received,
                history,
                own_previous,
                communicable_outputs
            )
            messages.append(HumanMessage(content=human_content))
            
            return {"messages": messages}
        
        return pre_model_hook
    
    
    def create_react_agent_instance(self, state: StaticGlobalState):
        """Create LangGraph react agent with current state context."""
        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            pre_model_hook=self.create_agent_pre_model_hook(state),
            response_format=self.output_class,
            checkpointer=InMemorySaver()
        )
    
    async def process(self, state: StaticGlobalState) -> StaticGlobalState:
        """Process the agent's task using LangGraph's create_react_agent."""
        current_iter = state.current_iteration
        
        # Check if we have a task
        task = self.get_task_for_current_iteration(state)
        if not task:
            return state
        
        # Check dependencies
        if not self.check_dependencies_ready(state):
            self.debug_dependencies(state)
            return state
        
        # Check if already processed
        outputs_dict = getattr(state, f"{self.name}_outputs")
        if current_iter in outputs_dict:
            return state
        
        try:
            # Create agent with current state context
            agent = self.create_react_agent_instance(state)
            
            # Run the agent
            config = {"configurable": {"thread_id": f"{self.name}_{current_iter}"}}
            result = await agent.ainvoke({"messages": []}, config)
            
            # Extract structured output
            structured_output = result.get("structured_response")
            if structured_output:
                structured_output.iteration = current_iter
                outputs_dict[current_iter] = structured_output
                
                # Only update last_update_iteration if this represents a real change
                if self.should_update_last_iteration(state, structured_output):
                    state.last_update_iteration[self.name] = current_iter
                
                # Send messages if any
                if structured_output.messages:
                    self.send_messages(state, structured_output.messages)
            
        except Exception as e:
            print(f"❌ {self.name} ERROR in iteration {current_iter}: {e}")
            import traceback
            traceback.print_exc()
        
        return state