"""Static workflow with checkpointing for the UAV design system."""

import asyncio
import time
from typing import Literal, List

import sys
import os

# Add paths for imports
current_dir = os.path.dirname(__file__)
backend_dir = os.path.dirname(current_dir)
project_dir = os.path.dirname(backend_dir)

sys.path.append(backend_dir)
sys.path.append(project_dir)

from langgraph.state import StaticGlobalState
from agents.mission_planner import MissionPlannerAgent
from agents.aerodynamics import AerodynamicsAgent  
from agents.propulsion import PropulsionAgent
from agents.structures import StructuresAgent
from agents.manufacturing import ManufacturingAgent
from agents.coordinator import CoordinatorAgent

from tools import (
    MISSION_PLANNER_TOOLS,
    AERODYNAMICS_TOOLS,
    PROPULSION_TOOLS,
    STRUCTURES_TOOLS,
    MANUFACTURING_TOOLS
)
from config import get_llm

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver


async def aggregator_node(state: StaticGlobalState) -> StaticGlobalState:
    """Run all static agents concurrently with checkpointing."""
    current_iter = state.current_iteration
    
    # Update progress file - agents starting processing 
    # If workflow was resuming, transition to running status
    if getattr(state, 'workflow_status', None) == "resuming":
        state.update_progress_file(status="running", current_agent="agents_starting")
    else:
        state.update_progress_file(current_agent="agents_starting")
    
    # Track tool usage before processing this iteration
    tools_before = state.get_total_tool_calls()
    
    llm = get_llm()
    
    # Create static agents with their specific tools
    agents = [
        MissionPlannerAgent(llm, MISSION_PLANNER_TOOLS),
        AerodynamicsAgent(llm, AERODYNAMICS_TOOLS),
        PropulsionAgent(llm, PROPULSION_TOOLS),
        StructuresAgent(llm, STRUCTURES_TOOLS),
        ManufacturingAgent(llm, MANUFACTURING_TOOLS)
    ]
    
    # Update progress file - agents actively processing
    state.update_progress_file(current_agent="agents_processing")
    
    # Run all agents concurrently
    await asyncio.gather(*[agent.process(state) for agent in agents])
    
    # Update progress file - agents completed (with all current metrics)
    state.update_progress_file(current_agent="agents_completed")
    
    # Also update the internal progress fields for consistency
    state.current_agent_processing = "agents_completed"
    state.last_progress_update = time.time()
    
    # Print iteration summary
    print(f"\n📊 ITERATION {current_iter} SUMMARY:")
    agent_names = ["mission_planner", "aerodynamics", "propulsion", "structures", "manufacturing"]
    for agent_name in agent_names:
        outputs_dict = getattr(state, f"{agent_name}_outputs")
        if current_iter in outputs_dict:
            # Check if this was an update or maintain
            if state.last_update_iteration[agent_name] == current_iter:
                status = "✅ OUTPUT (UPDATED)"
            else:
                status = "✅ OUTPUT (MAINTAINED)"
        else:
            status = "❌ NO OUTPUT"
        print(f"   {agent_name}: {status}")
    
    # Calculate iteration metrics
    iteration_messages = 0
    for chat in state.chats.values():
        iteration_messages += len(chat.get_messages_for_iteration(current_iter))
    
    # Get tools used in this iteration (difference from before)
    tools_after = state.get_total_tool_calls()
    iteration_tools = tools_after - tools_before
    
    # Get total counts
    total_chats = len(state.chats)
    total_messages = sum(len(chat.messages) for chat in state.chats.values())
    total_tools_used = tools_after
    
    print(f"   💬 Messages this iteration: {iteration_messages}")
    print(f"   🔧 Tools this iteration: {iteration_tools}")
    print(f"   💬 Total chats active: {total_chats}")
    print(f"   📨 Total messages: {total_messages}")
    print(f"   🔧 Total tools used: {total_tools_used}")
    
    return state


async def coordinator_node(state: StaticGlobalState) -> StaticGlobalState:
    """Coordinator evaluation and decision."""
    # Update progress file - coordinator processing
    state.update_progress_file(current_agent="coordinator")
    
    # Update internal fields for consistency
    state.current_agent_processing = "coordinator"
    state.last_progress_update = time.time()
    
    llm = get_llm()
    coordinator = CoordinatorAgent(llm)
    result = await coordinator.process(state)
    
    # Debug: Show current state before routing decision
    print(f"🔍 COORDINATOR ROUTING: current_iteration={result.current_iteration}, max_iterations={result.max_iterations}, project_complete={result.project_complete}")
    
    # Check if we should wait for user decision (max iterations OR coordinator says complete)
    # Check if we've completed all iterations (after current iteration finishes)
    if result.current_iteration >= result.max_iterations:
        print(f"🔄 Reached max iterations ({result.max_iterations}). Waiting for user decision...")
        result.waiting_for_user_decision = True
        result.workflow_status = "waiting_for_user"
        result.update_progress_file(current_agent="coordinator_waiting", status="waiting_for_user")
        result.current_agent_processing = "coordinator_waiting"
    elif result.project_complete:
        print(f"✅ Coordinator decided project complete. Waiting for user decision...")
        result.waiting_for_user_decision = True  
        result.workflow_status = "waiting_for_user"
        result.update_progress_file(current_agent="coordinator_waiting", status="waiting_for_user")
        result.current_agent_processing = "coordinator_waiting"
    else:
        # Normal continuation - increment iteration and continue to aggregator
        result.current_iteration += 1
        print(f"🔧 Coordinator: Incremented iteration to {result.current_iteration} and continuing to aggregator")
        result.update_progress_file(current_agent="coordinator_continuing")
        result.current_agent_processing = "coordinator_continuing"
    
    result.last_progress_update = time.time()
    return result


async def waiting_node(state: StaticGlobalState) -> StaticGlobalState:
    """Wait for user decision and handle continue/start_new."""
    print(f"⏳ Workflow waiting for user decision at iteration {state.current_iteration}/{state.max_iterations}")
    
    # Write progress file to signal UI that we're waiting
    state.update_progress_file(
        status="waiting_for_user", 
        current_agent="waiting_for_user_decision",
        iteration=state.current_iteration
    )
    
    # Wait for UI to set user_decision
    while not hasattr(state, 'user_decision') or state.user_decision is None:
        await asyncio.sleep(1)
        # Re-read progress file to check for user decision from UI
        progress_data = state.read_progress_file()
        if progress_data and progress_data.get('user_decision'):
            state.user_decision = progress_data['user_decision']
            if progress_data.get('additional_requirements'):
                state.additional_requirements = progress_data['additional_requirements']
            if progress_data.get('new_max_iterations'):
                state.max_iterations = progress_data['new_max_iterations']
    
    if state.user_decision == "continue":
        print(f"🔄 User chose to continue workflow. Adding requirements and updating max iterations...")
        # Update requirements and max_iterations (set by UI)
        state.user_requirements += f"\n\nADDITIONAL REQUIREMENTS:\n{state.additional_requirements}"
        state.waiting_for_user_decision = False
        state.project_complete = False
        # current_iteration stays same - continue from where we left off
        
        state.user_decision = None  # Reset
        print(f"🚀 Continuing workflow from iteration {state.current_iteration} with new max {state.max_iterations}")
        
    elif state.user_decision == "start_new":
        print(f"🆕 User chose to start new workflow. Ending current workflow...")
        state.project_complete = True
        state.workflow_status = "completed"
    
    return state


def should_continue(state: StaticGlobalState) -> Literal["continue", "wait"]:
    """Route from coordinator - NEVER goes to END."""
    if getattr(state, 'waiting_for_user_decision', False):
        return "wait"
    return "continue"


def create_static_uav_design_workflow() -> CompiledStateGraph:
    """Create the static LangGraph workflow with checkpointing."""
    
    # Create workflow with checkpointing
    workflow = StateGraph(StaticGlobalState)
    
    # Add nodes
    workflow.add_node("coordinator", coordinator_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("waiting", waiting_node)  # NEW waiting node
    
    # Set entry point
    workflow.set_entry_point("coordinator")
    
    # Coordinator routing - NEVER goes to END
    workflow.add_conditional_edges(
        "coordinator",
        should_continue,
        {
            "continue": "aggregator",
            "wait": "waiting"
        }
    )
    
    # Add edge back to coordinator after aggregator completes
    workflow.add_edge("aggregator", "coordinator")
    
    # Waiting node routing - ONLY from waiting node can we go to END
    workflow.add_conditional_edges(
        "waiting",
        lambda state: "continue" if not state.project_complete else "end",
        {
            "continue": "coordinator",  # Back to coordinator with updated state
            "end": END  # ONLY from waiting node
        }
    )
    
    # Compile with memory saver for checkpointing
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


async def run_static_workflow(
    user_requirements: str,
    thread_id: str = "static_uav_design",
    max_iterations: int = 10,
    shared_state: StaticGlobalState = None
) -> StaticGlobalState:
    """Run the static workflow with checkpointing."""
    
    # Create workflow
    workflow = create_static_uav_design_workflow()
    
    # Use shared state if provided, otherwise create new one
    if shared_state is not None:
        initial_state = shared_state
        # Update with new requirements and settings
        initial_state.user_requirements = user_requirements
        initial_state.max_iterations = max_iterations
        initial_state.thread_id = thread_id
        initial_state.update_progress_file(status="running", iteration=0)
    else:
        # Initialize new state
        initial_state = StaticGlobalState(
            user_requirements=user_requirements,
            max_iterations=max_iterations,
            thread_id=thread_id
        )
        initial_state.update_progress_file(status="running", iteration=0)
    
    # Reset chats for fresh start (only if starting new workflow, not resuming)
    if shared_state is None:
        initial_state.reset_chats()
    else:
        # Keep existing chats when using shared state
        pass
    
    # Configuration for checkpointing
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    # Run workflow with checkpointing
    final_state = None
    async for step in workflow.astream(initial_state, config):
        print(f"🔄 Workflow step: {list(step.keys())}")
        step_state = list(step.values())[0]
        
        # Convert dict to StaticGlobalState if needed
        if isinstance(step_state, dict):
            final_state = StaticGlobalState(**step_state)
        else:
            final_state = step_state
        
        # Update progress after each step
        final_state.last_progress_update = time.time()
        
        # Write comprehensive progress file after each step
        final_state.write_progress_file()
        
        # Update checkpoint metadata
        if hasattr(final_state, 'checkpoint_metadata'):
            final_state.checkpoint_metadata.update({
                "last_updated": asyncio.get_event_loop().time(),
                "step_count": final_state.current_iteration,
                "thread_id": thread_id
            })
        
        # If using shared state, sync all progress data
        if shared_state is not None:
            shared_state.current_iteration = final_state.current_iteration
            shared_state.project_complete = final_state.project_complete
            shared_state.last_update_iteration = final_state.last_update_iteration
            shared_state.tools_usage = final_state.tools_usage
            shared_state.chats = final_state.chats
            shared_state.current_agent_processing = getattr(final_state, 'current_agent_processing', None)
            shared_state.workflow_status = getattr(final_state, 'workflow_status', 'running')
            shared_state.last_progress_update = time.time()
            shared_state.write_progress_file()
    
    # Final progress update to file
    if final_state:
        status = "completed" if final_state.project_complete else "completed"
        final_state.update_progress_file(status=status, current_agent=None)
        if shared_state is not None:
            shared_state.update_progress_file(status=status, current_agent=None)
        
        # Print final workflow summary
        print(f"\n🎉 WORKFLOW COMPLETED!")
        print(f"=" * 50)
        print(f"📊 FINAL TOTALS:")
        print(f"   🔄 Total iterations: {final_state.current_iteration}")
        print(f"   🔧 Total tools used: {final_state.get_total_tool_calls()}")
        print(f"   💬 Total chats created: {len(final_state.chats)}")
        print(f"   📨 Total messages sent: {sum(len(chat.messages) for chat in final_state.chats.values())}")
        print(f"   ✅ Project complete: {final_state.project_complete}")
        
        # Tools breakdown from actual tool counters
        tool_counts = final_state.get_current_tool_counts()
        if tool_counts and any(count > 0 for count in tool_counts.values()):
            print(f"\n🔧 TOOLS BREAKDOWN:")
            for tool, count in tool_counts.items():
                if count > 0:  # Only show tools that were actually used
                    print(f"   {tool}: {count}")
        
        # Communication breakdown
        print(f"\n💬 COMMUNICATION BREAKDOWN:")
        for chat_key, chat in final_state.chats.items():
            if chat.messages:
                participants = " ↔️ ".join(chat.participants)
                print(f"   {participants}: {len(chat.messages)} messages")
        
        print(f"=" * 50)
    
    return final_state




async def get_workflow_history(thread_id: str) -> List[StaticGlobalState]:
    """Get the history of states for a workflow thread."""
    
    # Create workflow
    workflow = create_static_uav_design_workflow()
    
    # Configuration
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    # Get state history
    try:
        history = []
        async for state_snapshot in workflow.aget_state_history(config):
            history.append(state_snapshot.values)
        return history
    except Exception as e:
        print(f"❌ Error getting workflow history: {e}")
        return []