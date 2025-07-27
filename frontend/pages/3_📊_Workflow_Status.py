"""Workflow Status page - Monitor execution progress and system status."""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
import time
import asyncio

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.append(str(backend_path))

from langgraph.state import StaticGlobalState
from langgraph.workflow import run_static_workflow

# Page configuration
st.set_page_config(
    page_title="Workflow Status - Static Agent Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_file = Path(__file__).parent.parent / "assets" / "styles.css"
if css_file.exists():
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Helper functions
def get_agent_display_name(agent_name):
    """Get display name for agent."""
    agent_names = {
        "coordinator": "👥 Coordinator",
        "mission_planner": "🎯 Mission Planner", 
        "aerodynamics": "🌊 Aerodynamics",
        "propulsion": "🚀 Propulsion",
        "structures": "🏗️ Structures",
        "manufacturing": "🏭 Manufacturing"
    }
    return agent_names.get(agent_name, f"🤖 {agent_name.title()}")

def format_timestamp(timestamp):
    """Format timestamp for display."""
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Unknown"

# Header
st.markdown("""
<div class="main-header">
    <div class="header-content">
        <h1>📊 Workflow Status</h1>
        <p>Execute UAV design workflows and monitor system status</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize or get state from session
if 'workflow_state' not in st.session_state:
    st.session_state.workflow_state = StaticGlobalState()
    st.session_state.workflow_running = False
    st.session_state.workflow_thread_id = None
    st.session_state.workflow_completed = False

# Check if the state object has the reset_chats method and tools_usage, if not recreate it
# BUT respect the protection flag for completed workflows
should_recreate = (
    not hasattr(st.session_state.workflow_state, 'reset_chats') or 
    not hasattr(st.session_state.workflow_state, 'tools_usage')
)

if should_recreate and not st.session_state.get('workflow_data_preserved', False):
    # Preserve existing data when recreating state
    old_state = st.session_state.workflow_state
    st.session_state.workflow_state = StaticGlobalState()
    
    # Transfer any existing data
    if hasattr(old_state, 'chats') and old_state.chats:
        st.session_state.workflow_state.chats = old_state.chats
    if hasattr(old_state, 'current_iteration'):
        st.session_state.workflow_state.current_iteration = old_state.current_iteration
    if hasattr(old_state, 'project_complete'):
        st.session_state.workflow_state.project_complete = old_state.project_complete
    if hasattr(old_state, 'tools_usage') and old_state.tools_usage:
        st.session_state.workflow_state.tools_usage = old_state.tools_usage
    if hasattr(old_state, 'last_update_iteration'):
        st.session_state.workflow_state.last_update_iteration = old_state.last_update_iteration
elif should_recreate and st.session_state.get('workflow_data_preserved', False):
    print("🔒 Protected: Skipping state recreation for completed workflow with preserved data")

# Get read-only reference to state (UI should not modify this)
state = st.session_state.workflow_state

# Ensure state has progress tracking capabilities (backward compatibility)
if not hasattr(state, 'workflow_status'):
    state.workflow_status = "inactive"
if not hasattr(state, 'current_agent_processing'):
    state.current_agent_processing = None
if not hasattr(state, 'workflow_error'):
    state.workflow_error = None
if not hasattr(state, 'last_progress_update'):
    state.last_progress_update = time.time()

# Real workflow execution status monitoring with live progress
if st.session_state.get('workflow_running', False):
    try:
        # Create progress containers for real-time updates
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            # Read progress from file (updated by background thread)
            progress_snapshot = {}
            try:
                # Get thread ID for the current workflow
                workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
                
                # Create a temporary state to read the progress file
                from langgraph.state import StaticGlobalState
                temp_state = StaticGlobalState(thread_id=workflow_thread_id)
                progress_snapshot = temp_state.read_progress_file()
                
                # If no file exists or empty, use session state as fallback
                if not progress_snapshot:
                    progress_snapshot = {
                        "status": "running",
                        "current_iteration": state.current_iteration,
                        "max_iterations": state.max_iterations,
                        "current_agent": None,
                        "project_complete": state.project_complete,
                        "error": None,
                        "progress_percent": (state.current_iteration / state.max_iterations * 100) if state.max_iterations > 0 else 0
                    }
                else:
                    # SINGLE SOURCE OF TRUTH: Progress file data takes precedence during execution
                    # Update session state to match progress file (read-only synchronization)
                    if progress_snapshot.get('current_iteration') is not None:
                        st.session_state.workflow_state.current_iteration = progress_snapshot['current_iteration']
                    if progress_snapshot.get('max_iterations') is not None:
                        st.session_state.workflow_state.max_iterations = progress_snapshot['max_iterations']
                    if progress_snapshot.get('project_complete') is not None:
                        st.session_state.workflow_state.project_complete = progress_snapshot['project_complete']
                    if progress_snapshot.get('tools_usage'):
                        st.session_state.workflow_state.tools_usage = progress_snapshot['tools_usage']
                    
                    # Synchronize workflow status from progress file
                    workflow_status = progress_snapshot.get('status', 'running')
                    print(f"📊 Progress sync: status={workflow_status}, iter={progress_snapshot.get('current_iteration')}, running={st.session_state.get('workflow_running')}")
                    
                    # Sync chat data during execution
                    if progress_snapshot.get('full_chats'):
                        from langgraph.state import AgentChat, ChatMessage
                        for chat_key, chat_data in progress_snapshot['full_chats'].items():
                            if chat_key not in st.session_state.workflow_state.chats:
                                chat = AgentChat(
                                    participants=chat_data['participants'],
                                    chat_type=chat_data['chat_type'],
                                    last_activity=chat_data.get('last_activity')
                                )
                                for msg_data in chat_data['messages']:
                                    message = ChatMessage(
                                        id=msg_data['id'],
                                        from_agent=msg_data['from_agent'],
                                        to_agent=msg_data['to_agent'],
                                        content=msg_data['content'],
                                        timestamp=msg_data['timestamp'],
                                        iteration=msg_data['iteration'],
                                        message_type=msg_data['message_type'],
                                        metadata=msg_data.get('metadata', {})
                                    )
                                    chat.messages.append(message)
                                st.session_state.workflow_state.chats[chat_key] = chat
                    
                    # Check if workflow completed or waiting for user
                    # SIMPLE LOGIC: Only change UI state if user hasn't explicitly set workflow_running=True
                    workflow_status = progress_snapshot.get('status')
                    ui_running = st.session_state.get('workflow_running', False)
                    print(f"🔍 Status check: workflow_status={workflow_status}, ui_running={ui_running}")
                    
                    if workflow_status == 'waiting_for_user' and not st.session_state.get('workflow_running', False):
                        # Natural transition: workflow reached waiting state and UI is not explicitly running
                        st.session_state.workflow_waiting_for_user = True
                        st.session_state.workflow_running = False
                        print(f"🔄 Natural transition: workflow reached waiting state")
                    elif workflow_status != 'waiting_for_user' and st.session_state.get('workflow_waiting_for_user', False):
                        print(f"🚀 Workflow status changed to {workflow_status} - clearing waiting state")
                        st.session_state.workflow_waiting_for_user = False
                        if workflow_status == 'running':
                            st.session_state.workflow_running = True
                    elif progress_snapshot.get('status') == 'completed' and progress_snapshot.get('project_complete'):
                        # Only truly completed if both status is completed AND project_complete is True
                        st.session_state.workflow_completed = True
                        st.session_state.workflow_running = False
            except Exception as e:
                # Fallback for any errors
                progress_snapshot = {
                    "status": "running",
                    "current_iteration": state.current_iteration,
                    "max_iterations": state.max_iterations,
                    "current_agent": None,
                    "project_complete": state.project_complete,
                    "error": None,
                    "progress_percent": (state.current_iteration / state.max_iterations * 100) if state.max_iterations > 0 else 0
                }
        
        # Show workflow progress
        if progress_snapshot["status"] == "resuming":
            progress_percent = progress_snapshot["progress_percent"]
            st.progress(progress_percent / 100, f"Resuming Workflow: {progress_percent:.1f}% (From Iteration {progress_snapshot['current_iteration']}/{progress_snapshot['max_iterations']})")
            st.info("🔄 **Resuming workflow** with additional requirements...")
            
        elif progress_snapshot["status"] == "running":
            progress_percent = progress_snapshot["progress_percent"]
            st.progress(progress_percent / 100, f"Live Progress: {progress_percent:.1f}% (Iteration {progress_snapshot['current_iteration']}/{progress_snapshot['max_iterations']})")
            
            # Show current activity
            current_agent = progress_snapshot.get("current_agent")
            if current_agent == "coordinator":
                st.info("🎯 **Coordinator** is evaluating workflow progress...")
            elif current_agent == "agents_starting":
                st.info("🚀 **Agents** are starting processing...")
            elif current_agent == "agents_processing":
                st.info("⚙️ **All Agents** are actively processing with LLMs...")
            elif current_agent == "agents_completed":
                st.info("✅ **Agents** completed iteration processing")
            elif current_agent == "coordinator_continuing":
                st.info("🔄 **Coordinator** decided to continue to next iteration")
            else:
                st.info(f"🔄 Iteration {progress_snapshot['current_iteration']} - Workflow in progress...")
        
        elif progress_snapshot["status"] == "waiting_for_user":
            st.warning("⏳ Workflow is waiting for your decision!")
            st.info("The workflow has reached max iterations or coordinator decided it's complete. Please scroll down to choose how to proceed.")
            
        elif progress_snapshot["status"] == "completed" and progress_snapshot.get("project_complete"):
            st.success("🎉 Workflow completed successfully!")
            # Update session state and cleanup
            st.session_state.workflow_running = False
            st.session_state.workflow_started = False
            st.session_state.workflow_completed = True
            
            # CRITICAL: Sync ALL workflow data to session state before cleanup
            try:
                workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
                from langgraph.state import StaticGlobalState
                
                # Create temp state to read final workflow data
                final_workflow_state = StaticGlobalState(thread_id=workflow_thread_id)
                final_progress_data = final_workflow_state.read_progress_file()
                
                if final_progress_data:
                    # Sync all available data from progress file
                    if final_progress_data.get('current_iteration'):
                        state.current_iteration = final_progress_data['current_iteration']
                    if final_progress_data.get('project_complete'):
                        state.project_complete = True
                    if final_progress_data.get('last_update_iteration'):
                        state.last_update_iteration = final_progress_data['last_update_iteration']
                    if final_progress_data.get('tools_usage'):
                        state.tools_usage = final_progress_data['tools_usage']
                    else:
                        # Ensure tools_usage exists even if empty
                        state.tools_usage = {}
                    
                    # Sync chat data if available
                    if final_progress_data.get('full_chats'):
                        # Reconstruct chats from serialized data
                        state.chats = {}
                        for chat_key, chat_data in final_progress_data['full_chats'].items():
                            from langgraph.state import AgentChat, ChatMessage
                            
                            # Create AgentChat object
                            chat = AgentChat(
                                participants=chat_data['participants'],
                                chat_type=chat_data['chat_type'],
                                last_activity=chat_data.get('last_activity')
                            )
                            
                            # Reconstruct messages
                            for msg_data in chat_data['messages']:
                                message = ChatMessage(
                                    id=msg_data['id'],
                                    from_agent=msg_data['from_agent'],
                                    to_agent=msg_data['to_agent'],
                                    content=msg_data['content'],
                                    timestamp=msg_data['timestamp'],
                                    iteration=msg_data['iteration'],
                                    message_type=msg_data['message_type'],
                                    metadata=msg_data.get('metadata', {})
                                )
                                chat.messages.append(message)
                            
                            state.chats[chat_key] = chat
                    
                    # NOTE: Do NOT call sync_complete_data_to_state() here!
                    # final_workflow_state is an EMPTY state object, calling sync would wipe our data
                    # All data comes from manual reconstruction above from progress file
                    
                    print(f"✅ Manual reconstruction complete: {len(state.chats)} chats, {len(state.tools_usage or {})} tools")
                    
                    # Force session state to reflect the synced data immediately
                    st.session_state.workflow_state = state
                    
                    # Set a flag to prevent future resets of completed workflow data
                    st.session_state.workflow_data_preserved = True
                    
                    print(f"✅ Session state updated with synced data: {len(st.session_state.workflow_state.chats)} chats")
                    print(f"✅ Protection flag set to preserve completed workflow data")
                
                # Now cleanup progress file
                final_workflow_state.cleanup_progress_file()
                
            except Exception as e:
                print(f"❌ Error syncing workflow data before cleanup: {e}")
                st.error(f"Warning: Could not preserve all workflow data: {e}")
            
        elif progress_snapshot["status"] == "error":
            st.error(f"❌ Workflow failed: {progress_snapshot.get('error', 'Unknown error')}")
            # Update session state and cleanup
            st.session_state.workflow_running = False
            st.session_state.workflow_started = False
            st.session_state.workflow_error = progress_snapshot.get('error', 'Unknown error')
            
            # Cleanup progress file on error
            try:
                workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
                from langgraph.state import StaticGlobalState
                cleanup_state = StaticGlobalState(thread_id=workflow_thread_id)
                cleanup_state.cleanup_progress_file()
            except Exception as e:
                print(f"❌ Error cleaning up progress file: {e}")
    
        with status_container:
            # Show live agent activity (if we have current agent info)
            current_agent = progress_snapshot.get("current_agent")
            if current_agent and current_agent not in ["coordinator", "agents_starting", "agents_processing", "agents_completed"]:
                st.caption(f"Currently active: **{current_agent.replace('_', ' ').title()}**")
        
        # Handle workflow errors
        if st.session_state.get('workflow_error'):
            st.error(f"❌ Workflow failed: {st.session_state.workflow_error}")
            st.session_state.workflow_running = False
            st.session_state.workflow_started = False
            
    except Exception as e:
        # ERROR BOUNDARY: Handle any errors in workflow monitoring
        st.error(f"❌ Error in workflow monitoring: {e}")
        st.session_state.workflow_error = f"UI monitoring error: {e}"
        st.session_state.workflow_running = False
        print(f"❌ Workflow monitoring error: {e}")
        import traceback
        traceback.print_exc()

# Main workflow controls section - FIRST
st.markdown("## 🎯 Workflow Controls")

# Check workflow status with validation
workflow_running = st.session_state.get('workflow_running', False)
workflow_completed = st.session_state.get('workflow_completed', False)
workflow_waiting = st.session_state.get('workflow_waiting_for_user', False)

# DEFENSIVE PROGRAMMING: Validate state consistency
if workflow_running and workflow_completed:
    print("⚠️ INVALID STATE: workflow_running=True AND workflow_completed=True")
    st.session_state.workflow_completed = False
    
if workflow_running and workflow_waiting:
    print("⚠️ INVALID STATE: workflow_running=True AND workflow_waiting=True") 
    st.session_state.workflow_waiting_for_user = False
    
print(f"🔍 UI State: running={workflow_running}, completed={workflow_completed}, waiting={workflow_waiting}")

# Handle completed workflow first
if workflow_completed and not workflow_running:
    st.success("🎉 Workflow Completed Successfully!")
    
    # Show completion summary with enhanced statistics
    progress_info = state.get_workflow_progress()
    
    st.markdown("### 📊 Final Results Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Iterations", state.current_iteration)
    with col2:
        st.metric("Messages Exchanged", progress_info["total_messages"])
    with col3:
        st.metric("Tools Used", progress_info.get("total_tools_used", 0))
    with col4:
        st.metric("Conversations", progress_info["total_chats"])
    
    # Tools usage breakdown
    if progress_info.get("tools_breakdown"):
        st.markdown("### 🔧 Tools Usage Breakdown")
        tools_col1, tools_col2 = st.columns(2)
        
        tools_items = list(progress_info["tools_breakdown"].items())
        mid_point = len(tools_items) // 2
        
        with tools_col1:
            for tool, count in tools_items[:mid_point]:
                st.metric(tool.replace("_", " ").title(), count)
        
        with tools_col2:
            for tool, count in tools_items[mid_point:]:
                st.metric(tool.replace("_", " ").title(), count)
    
    # Show final agent outputs
    st.markdown("### 📋 Final Agent Outputs")
    agent_names = ["mission_planner", "aerodynamics", "propulsion", "structures", "manufacturing"]
    
    output_tabs = st.tabs([get_agent_display_name(name) for name in agent_names])
    
    for i, agent_name in enumerate(agent_names):
        with output_tabs[i]:
            outputs_dict = getattr(state, f"{agent_name}_outputs", {})
            if outputs_dict:
                latest_iteration = max(outputs_dict.keys())
                latest_output = outputs_dict[latest_iteration]
                
                st.markdown(f"**Final Output (Iteration {latest_iteration}):**")
                if hasattr(latest_output, 'dict'):
                    output_dict = latest_output.dict()
                    # Remove large fields for summary
                    summary_dict = {k: v for k, v in output_dict.items() 
                                  if k not in ['messages', 'detailed_analysis']}
                    st.json(summary_dict)
                else:
                    st.write(str(latest_output))
            else:
                st.info(f"No outputs generated by {get_agent_display_name(agent_name)}")

# Handle workflow waiting for user decision
if st.session_state.get('workflow_waiting_for_user', False):
    st.markdown("### ⏳ Workflow Waiting for Your Decision")
    
    # Determine the specific reason for waiting
    current_iter = state.current_iteration
    max_iter = state.max_iterations
    project_complete = state.project_complete
    
    if current_iter >= max_iter:
        st.warning(f"🔄 Workflow has reached the maximum iterations limit ({current_iter}/{max_iter}). Choose how to proceed:")
    elif project_complete:
        st.warning(f"✅ Coordinator has decided the project is complete at iteration {current_iter}/{max_iter}. Choose how to proceed:")
    else:
        st.warning("⏳ Workflow is waiting for your decision. Choose how to proceed:")
    
    decision_col1, decision_col2 = st.columns(2)
    
    with decision_col1:
        st.markdown("#### 🔄 Continue Current Workflow")
        st.info("Add additional requirements and continue with existing context.")
        
        additional_requirements = st.text_area(
            "Additional Requirements",
            placeholder="Enter additional requirements or modifications...",
            height=100,
            key="waiting_additional_reqs"
        )
        
        current_max = state.max_iterations
        current_iter = state.current_iteration
        
        additional_iterations = st.slider(
            "Additional Iterations",
            min_value=1,
            max_value=50,
            value=5,
            help=f"Add iterations to current max ({current_max})",
            key="waiting_additional_iterations"
        )
        
        new_max = current_max + additional_iterations
        st.info(f"📊 {current_iter}/{current_max} → {current_iter}/{new_max} (added {additional_iterations})")
        
        if st.button("🔄 Continue Workflow", key="continue_from_waiting", type="primary"):
            # Write user decision to progress file for workflow to pick up
            workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
            temp_state = StaticGlobalState(thread_id=workflow_thread_id)
            
            # Read existing progress data
            progress_data = temp_state.read_progress_file()
            if progress_data:
                # Add user decision data
                progress_data.update({
                    'user_decision': 'continue',
                    'additional_requirements': additional_requirements.strip() if additional_requirements.strip() else "Continue with current design",
                    'new_max_iterations': new_max
                })
                
                # Write back to progress file
                import json
                import tempfile
                file_path = temp_state.get_progress_file_path()
                with open(file_path, 'w') as f:
                    json.dump(progress_data, f, indent=2)
            
            # Update session state
            st.session_state.workflow_state.max_iterations = new_max
            st.session_state.workflow_waiting_for_user = False
            st.session_state.workflow_running = True
            
            st.success(f"✅ Continuing workflow with {additional_iterations} additional iterations!")
            st.rerun()
    
    with decision_col2:
        st.markdown("#### 🆕 Start New Workflow")
        st.info("End current workflow and start fresh.")
        
        if st.button("🆕 Start New Workflow", key="start_new_from_waiting", type="secondary"):
            # Write user decision to progress file
            workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
            temp_state = StaticGlobalState(thread_id=workflow_thread_id)
            
            # Read existing progress data
            progress_data = temp_state.read_progress_file()
            if progress_data:
                # Add user decision data
                progress_data['user_decision'] = 'start_new'
                
                # Write back to progress file
                import json
                file_path = temp_state.get_progress_file_path()
                with open(file_path, 'w') as f:
                    json.dump(progress_data, f, indent=2)
            
            # Update session state
            st.session_state.workflow_waiting_for_user = False
            st.session_state.workflow_completed = True
            st.session_state.workflow_running = False
            
            st.success("✅ Starting new workflow...")
            st.rerun()

elif st.session_state.get('workflow_completed', False):
    # Workflow control buttons
    st.markdown("### 🎯 What's Next?")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Continue with Current Design")
        st.info("Add additional requirements and continue refining this design with existing context and memory.")
        
        additional_requirements = st.text_area(
            "Additional Requirements", 
            placeholder="Enter additional requirements or modifications for the current design...",
            height=100,
            key="additional_reqs"
        )
        
        # Additional iterations slider
        current_max = st.session_state.workflow_state.max_iterations
        current_iter = st.session_state.workflow_state.current_iteration
        
        additional_iterations = st.slider(
            "Additional Iterations",
            min_value=1,
            max_value=50,
            value=10,
            help=f"Number of additional iterations to add to current max ({current_max}). New max will be {current_max} + selected value."
        )
        
        st.info("ℹ️ This section has been simplified. Use the continue workflow option when the workflow is waiting for user decision.")
    
    with col2:
        st.markdown("#### Start Fresh Design")
        st.info("Begin a completely new UAV design workflow with fresh memory and requirements.")
        
        if st.button("🆕 Start New Workflow", use_container_width=True, type="primary"):
            # Reset all session state
            for key in list(st.session_state.keys()):
                if key.startswith('workflow_'):
                    del st.session_state[key]
            
            # Clear protection flag
            st.session_state.workflow_data_preserved = False
            
            # Reset state object completely
            st.session_state.workflow_state = StaticGlobalState()
            st.success("✅ System reset! Ready for new workflow.")
            st.rerun()
    
    st.markdown("---")

elif not workflow_running:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # User requirements input
        user_requirements = st.text_area(
            "UAV Design Requirements", 
            placeholder="Enter your UAV design requirements here...\nExample: Design a surveillance UAV with 2-hour flight time, 50km range, and 2kg payload capacity.",
            height=120,
            help="Describe the specifications and constraints for your UAV design"
        )
    
    with col2:
        st.markdown("#### Settings")
        # Max iterations setting
        max_iterations = st.slider("Max Iterations", 1, 100, 10)
        
        # Thread ID input (optional)
        thread_id = st.text_input("Thread ID (optional)", value="static_uav_design")
    
    # Start workflow button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Start Workflow", use_container_width=True, type="primary", key="start_workflow_main"):
            if user_requirements.strip():
                try:
                    import asyncio
                    import threading
                    from langgraph.workflow import run_static_workflow
                except ImportError as e:
                    st.error(f"❌ Missing dependencies for real workflow execution: {e}")
                    st.error("Please ensure all dependencies are installed: `uv sync` or `pip install -r requirements.txt`")
                else:
                    # COMPREHENSIVE STATE CLEANUP FOR FRESH WORKFLOW
                    
                    # 1. Clear all workflow-related session state
                    workflow_keys = [key for key in st.session_state.keys() if key.startswith('workflow_')]
                    for key in workflow_keys:
                        del st.session_state[key]
                    
                    # 2. Clean up old progress files
                    import glob
                    import os
                    progress_files = glob.glob('/tmp/workflow_progress_*.json')
                    for file_path in progress_files:
                        try:
                            os.remove(file_path)
                            print(f"🧹 Cleaned up old progress file: {file_path}")
                        except Exception as e:
                            print(f"⚠️ Could not remove {file_path}: {e}")
                    
                    # 3. Reset state for fresh start
                    st.session_state.workflow_state = StaticGlobalState()
                    st.session_state.workflow_state.reset_chats_and_tools()
                    st.session_state.workflow_state.user_requirements = user_requirements
                    st.session_state.workflow_state.max_iterations = max_iterations
                    st.session_state.workflow_state.thread_id = thread_id
                    st.session_state.workflow_state.current_iteration = 0
                    st.session_state.workflow_state.project_complete = False
                    
                    # Clear previous outputs
                    st.session_state.workflow_state.mission_planner_outputs = {}
                    st.session_state.workflow_state.aerodynamics_outputs = {}
                    st.session_state.workflow_state.propulsion_outputs = {}
                    st.session_state.workflow_state.structures_outputs = {}
                    st.session_state.workflow_state.manufacturing_outputs = {}
                    st.session_state.workflow_state.coordinator_outputs = {}
                    
                    # Reset last update iterations
                    for agent_name in st.session_state.workflow_state.last_update_iteration.keys():
                        st.session_state.workflow_state.last_update_iteration[agent_name] = -1
                    
                    # 4. Initialize session state flags for fresh workflow
                    st.session_state.workflow_running = True
                    st.session_state.workflow_waiting_for_user = False
                    st.session_state.workflow_completed = False
                    st.session_state.workflow_started = True
                    st.session_state.workflow_requirements = user_requirements
                    st.session_state.workflow_max_iterations = max_iterations
                    st.session_state.workflow_thread_id = thread_id
                    st.session_state.workflow_error = None
                    st.session_state.workflow_data_preserved = False
                    st.session_state.last_seen_iteration = -1  # Initialize iteration tracking
                    
                    print(f"✅ Fresh workflow state initialized: running={st.session_state.workflow_running}, waiting={st.session_state.workflow_waiting_for_user}")
                    
                    # Start real workflow in background thread WITHOUT session state access
                    def run_workflow_background():
                        try:
                            # Create a standalone state for the background workflow
                            from langgraph.state import StaticGlobalState
                            workflow_state = StaticGlobalState(
                                user_requirements=user_requirements,
                                max_iterations=max_iterations,
                                thread_id=thread_id
                            )
                            
                            # Initialize progress file
                            workflow_state.update_progress_file(status="starting", iteration=0)
                            
                            # Run the actual workflow
                            final_state = asyncio.run(run_static_workflow(
                                user_requirements=user_requirements,
                                thread_id=thread_id,
                                max_iterations=max_iterations,
                                shared_state=workflow_state
                            ))
                            
                            # Write final completion to progress file
                            final_state.update_progress_file(status="completed")
                            
                        except Exception as e:
                            # Write error to progress file (no session state access)
                            try:
                                from langgraph.state import StaticGlobalState
                                error_state = StaticGlobalState(thread_id=thread_id)
                                error_state.update_progress_file(error=str(e), status="error")
                            except:
                                pass
                            print(f"❌ Workflow error: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # 5. Start background thread with proper cleanup
                    try:
                        # Kill any existing workflow threads first
                        if hasattr(st.session_state, 'workflow_thread') and st.session_state.workflow_thread:
                            if st.session_state.workflow_thread.is_alive():
                                print("🛑 Terminating existing workflow thread...")
                                # Note: Cannot force kill threads in Python, but they are daemon threads
                        
                        workflow_thread = threading.Thread(target=run_workflow_background, daemon=True)
                        workflow_thread.start()
                        st.session_state.workflow_thread = workflow_thread
                        print(f"🚀 Started new workflow thread: {workflow_thread.name}")
                        
                    except Exception as e:
                        st.error(f"❌ Failed to start workflow thread: {e}")
                        st.session_state.workflow_running = False
                        st.session_state.workflow_error = str(e)
                    
                    st.success("✅ Real workflow started! Agents are now processing with LLMs...")
                    st.rerun()
            else:
                st.error("Please enter UAV requirements before starting.")
else:
    # Show running status
    st.info(f"""
    **🔄 Workflow Running**: {st.session_state.get('workflow_thread_id', 'Unknown')}
    
    **Requirements**: {st.session_state.get('workflow_requirements', 'Not specified')[:150]}{'...' if len(st.session_state.get('workflow_requirements', '')) > 150 else ''}
    """)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🛑 Stop Workflow", use_container_width=True, type="secondary"):
            st.session_state.workflow_running = False
            st.session_state.workflow_started = False
            
            # Cleanup progress file when stopping manually
            try:
                workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
                from langgraph.state import StaticGlobalState
                cleanup_state = StaticGlobalState(thread_id=workflow_thread_id)
                cleanup_state.cleanup_progress_file()
            except Exception as e:
                print(f"❌ Error cleaning up progress file: {e}")
            
            st.success("✅ Workflow stopped and cleaned up.")
            st.rerun()

st.markdown("---")

# Sidebar for display settings only
with st.sidebar:
    st.markdown("### ⚙️ Display Settings")
    
    # Display options
    show_detailed_logs = st.checkbox("Show detailed iteration logs", value=False)
    show_agent_outputs = st.checkbox("Show agent output summaries", value=True)
    
    # Manual refresh
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.rerun()

# Get workflow progress
progress_info = state.get_workflow_progress()

# System status section
st.markdown("## 📈 System Status")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # Use real-time progress from file if available
    if workflow_running:
        try:
            workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
            from langgraph.state import StaticGlobalState
            temp_state = StaticGlobalState(thread_id=workflow_thread_id)
            file_progress = temp_state.read_progress_file()
            if file_progress:
                current_iter = file_progress["current_iteration"]
                max_iter = file_progress["max_iterations"]
                delta_text = f"Max: {max_iter} ({file_progress['progress_percent']:.1f}%)"
            else:
                current_iter = progress_info["current_iteration"]
                delta_text = f"Max: {progress_info['max_iterations']}"
        except Exception:
            current_iter = progress_info["current_iteration"]
            delta_text = f"Max: {progress_info['max_iterations']}"
    else:
        current_iter = progress_info["current_iteration"]
        delta_text = f"Max: {progress_info['max_iterations']}"
    
    st.metric(
        "Current Iteration", 
        current_iter,
        delta=delta_text
    )

with col2:
    if workflow_completed and not workflow_running:
        agent_status_text = "All Complete"
        agent_delta = "Finished"
    elif workflow_running:
        # Show real-time agent activity from file
        try:
            workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
            from langgraph.state import StaticGlobalState
            temp_state = StaticGlobalState(thread_id=workflow_thread_id)
            file_progress = temp_state.read_progress_file()
            current_agent = file_progress.get("current_agent", "") if file_progress else ""
        except Exception:
            current_agent = ""
        
        if current_agent == "coordinator":
            agent_status_text = "Coordinator"
            agent_delta = "Evaluating"
        elif current_agent == "agents_processing":
            agent_status_text = "All Agents"
            agent_delta = "Processing"
        elif current_agent == "agents_starting":
            agent_status_text = "All Agents"
            agent_delta = "Starting"
        else:
            agent_status_text = progress_info["active_agents"]
            agent_delta = "Active"
    else:
        agent_status_text = progress_info["active_agents"]
        agent_delta = "Ready"
    
    st.metric(
        "Active Agents",
        agent_status_text,
        delta=agent_delta
    )

with col3:
    # Use real-time tools usage from file if available
    if workflow_running:
        try:
            workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
            from langgraph.state import StaticGlobalState
            temp_state = StaticGlobalState(thread_id=workflow_thread_id)
            file_progress = temp_state.read_progress_file()
            tools_used = file_progress.get("total_tools_used", 0) if file_progress else 0
        except Exception:
            tools_used = progress_info.get("total_tools_used", 0)
    else:
        tools_used = progress_info.get("total_tools_used", 0)
    
    st.metric(
        "Tools Used",
        tools_used,
        delta="Total executions"
    )

with col4:
    # System status - inactive by default, running only when workflow is active
    if workflow_completed and not workflow_running:
        system_status = "🏁 Completed"
        status_delta = "Finished"
    elif workflow_running and st.session_state.get('workflow_started', False):
        system_status = "🔄 Running"
        status_delta = "Active"
    elif workflow_running:
        system_status = "⏳ Starting"  
        status_delta = "Initializing"
    else:
        system_status = "⭕ Inactive"
        status_delta = "Ready"
    
    st.metric(
        "System Status",
        system_status,
        delta=status_delta
    )


st.markdown("---")

# Agent status grid with live updates
st.markdown("## 🤖 Agent Status Overview")

# Get real-time progress for agent status from file
progress_snapshot = None
if workflow_running:
    try:
        workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
        from langgraph.state import StaticGlobalState
        temp_state = StaticGlobalState(thread_id=workflow_thread_id)
        progress_snapshot = temp_state.read_progress_file()
    except Exception:
        progress_snapshot = None

# Create agent status grid
agent_names = ["mission_planner", "aerodynamics", "propulsion", "structures", "manufacturing"]
cols = st.columns(3)

for i, agent_name in enumerate(agent_names):
    with cols[i % 3]:
        display_name = get_agent_display_name(agent_name)
        last_update = state.last_update_iteration.get(agent_name, -1)
        
        # Determine status based on real-time progress and workflow state
        if workflow_completed and not workflow_running:
            status = "🏁 Completed"
            status_class = "completed"
        elif workflow_running and progress_snapshot:
            current_agent = progress_snapshot.get("current_agent", "")
            workflow_status = progress_snapshot.get("status", "running")
            
            # Handle resuming status
            if workflow_status == "resuming":
                status = "🔄 Resuming"
                status_class = "starting"
            # Show real-time agent activity
            elif current_agent == "agents_processing":
                status = "⚙️ Processing"
                status_class = "processing"
            elif current_agent == "agents_starting":
                status = "🚀 Starting"
                status_class = "starting"
            elif current_agent == "agents_completed":
                status = "✅ Completed Iteration"
                status_class = "updated"
            elif last_update >= state.current_iteration - 1:
                status = "✅ Recently Active"
                status_class = "updated"
            elif last_update >= 0:
                status = "⏸️ Waiting"
                status_class = "maintained"
            else:
                status = "⭕ Not Started"
                status_class = "no-output"
        elif last_update == -1:
            status = "⭕ Not Started"
            status_class = "no-output"
        elif workflow_running:
            status = "⏸️ Idle"
            status_class = "maintained"
        else:
            status = "⭕ Inactive"
            status_class = "no-output"
        
        # Agent card
        st.markdown(f"""
        <div class="agent-card">
            <h4>{display_name}</h4>
            <div class="agent-output-status {status_class}">
                {status}
            </div>
            <div style="margin-top: 0.5rem; font-size: 0.9em;">
                Last Update: Iteration {last_update if last_update >= 0 else 'None'}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Iteration history
st.markdown("## 📚 Iteration History")

if state.current_iteration == 0:
    st.info("No iterations completed yet. History will appear as the workflow progresses.")
else:
    # Display recent iterations
    for iteration in range(max(0, state.current_iteration - 5), state.current_iteration + 1):
        summary = state.get_iteration_summary(iteration)
        
        with st.expander(f"📋 Iteration {iteration} Summary", expanded=(iteration == state.current_iteration)):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Agents Executed:** {len(summary['agents_executed'])}")
                if summary['agents_executed']:
                    for agent in summary['agents_executed']:
                        display_name = get_agent_display_name(agent)
                        st.markdown(f"• {display_name}")
                else:
                    st.markdown("• No agents executed")
            
            with col2:
                st.markdown(f"**Messages Sent:** {summary['messages_sent']}")
                st.markdown(f"**Status:** {'Current' if iteration == state.current_iteration else 'Completed'}")
            
            if show_detailed_logs:
                st.markdown("**Detailed Information:**")
                if iteration == state.current_iteration:
                    st.info("Current iteration in progress...")
                else:
                    st.success(f"Iteration {iteration} completed successfully")

# System performance metrics
st.markdown("---")
st.markdown("## ⚡ System Performance")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 💬 Communication Stats")
    
    # Use live data from file if workflow is running
    if workflow_running:
        try:
            workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
            from langgraph.state import StaticGlobalState
            temp_state = StaticGlobalState(thread_id=workflow_thread_id)
            file_progress = temp_state.read_progress_file()
            if file_progress:
                total_chats = file_progress.get("total_chats", 0)
                total_messages = file_progress.get("total_messages", 0)
            else:
                total_chats = progress_info["total_chats"]
                total_messages = progress_info["total_messages"]
        except Exception:
            total_chats = progress_info["total_chats"]
            total_messages = progress_info["total_messages"]
    else:
        total_chats = progress_info["total_chats"]
        total_messages = progress_info["total_messages"]
    
    st.metric("Total Chats", total_chats)
    st.metric("Total Messages", total_messages)

with col2:
    st.markdown("### 🔄 Execution Stats")
    
    # Use live iteration data from file if running
    if workflow_running:
        try:
            workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
            from langgraph.state import StaticGlobalState
            temp_state = StaticGlobalState(thread_id=workflow_thread_id)
            file_progress = temp_state.read_progress_file()
            if file_progress:
                current_iter = file_progress.get("current_iteration", state.current_iteration)
                max_iter = file_progress.get("max_iterations", state.max_iterations)
            else:
                current_iter = state.current_iteration
                max_iter = state.max_iterations
        except Exception:
            current_iter = state.current_iteration
            max_iter = state.max_iterations
    else:
        current_iter = state.current_iteration
        max_iter = state.max_iterations
    
    st.metric("Iterations Completed", current_iter)
    iterations_remaining = max(0, max_iter - current_iter)
    st.metric("Iterations Remaining", iterations_remaining)

with col3:
    st.markdown("### 🔧 Tools Statistics")
    
    # Use live tools data from file if running
    if workflow_running:
        try:
            workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
            from langgraph.state import StaticGlobalState
            temp_state = StaticGlobalState(thread_id=workflow_thread_id)
            file_progress = temp_state.read_progress_file()
            if file_progress:
                total_tools = file_progress.get("total_tools_used", 0)
                tools_breakdown = file_progress.get("tools_usage", {})
            else:
                total_tools = progress_info.get("total_tools_used", 0)
                tools_breakdown = progress_info.get("tools_breakdown", {})
        except Exception:
            total_tools = progress_info.get("total_tools_used", 0)
            tools_breakdown = progress_info.get("tools_breakdown", {})
    else:
        total_tools = progress_info.get("total_tools_used", 0)
        tools_breakdown = progress_info.get("tools_breakdown", {})
    
    st.metric("Total Tools Used", total_tools)
    if tools_breakdown:
        most_used_tool = max(tools_breakdown, key=tools_breakdown.get)
        st.metric("Most Used Tool", most_used_tool.replace("_", " ").title())
    else:
        st.metric("Most Used Tool", "None")

# Agent outputs section (if enabled)
if show_agent_outputs:
    st.markdown("---")
    st.markdown("## 📄 Agent Output Summaries")
    
    agent_outputs_found = False
    
    for agent_name in agent_names:
        outputs_dict = getattr(state, f"{agent_name}_outputs", {})
        if outputs_dict:
            agent_outputs_found = True
            display_name = get_agent_display_name(agent_name)
            
            with st.expander(f"📋 {display_name} Outputs"):
                for iteration, output in sorted(outputs_dict.items()):
                    st.markdown(f"**Iteration {iteration}:**")
                    if hasattr(output, 'dict'):
                        # Display structured output summary
                        output_dict = output.dict()
                        # Remove large fields for summary
                        summary_dict = {k: v for k, v in output_dict.items() 
                                      if k not in ['messages', 'detailed_analysis']}
                        st.json(summary_dict)
                    else:
                        st.write(str(output)[:200] + "..." if len(str(output)) > 200 else str(output))
    
    if not agent_outputs_found:
        st.info("No agent outputs available yet. Outputs will appear as agents complete their tasks.")

# Workflow configuration
with st.sidebar:
    st.markdown("### ⚙️ Workflow Configuration")
    st.info(f"""
    **Max Iterations:** {state.max_iterations}
    **Stability Threshold:** {state.stability_threshold}
    **Thread ID:** {state.thread_id if state.thread_id else 'Not set'}
    **Checkpointing:** Enabled
    """)
    
    st.markdown("### 📊 Current Status")
    if state.project_complete:
        st.success("🎉 Project Complete!")
    elif workflow_running and st.session_state.get('workflow_started', False):
        st.info("🔄 System Active")
    elif workflow_running:
        st.warning("⏳ System Starting")
    else:
        st.info("⭕ System Inactive")
    
    st.markdown("### 💡 Status Legend")
    st.markdown("""
    **Agent Status:**
    - ✅ **Active**: Recently updated
    - ⏸️ **Idle**: No recent updates
    - ⭕ **Not Started**: Never executed
    - 🏁 **Completed**: Workflow finished
    
    **System Status:**
    - ⭕ **Inactive**: Ready to run workflow
    - ⏳ **Starting**: Workflow initializing
    - 🔄 **Running**: Agents are processing
    - 🏁 **Complete**: Workflow finished
    """)

# Live updates - automatically refresh when real workflow is running
if st.session_state.get('workflow_running', False):
    # Refresh every 2 seconds to monitor real workflow progress
    time.sleep(2.0)  # Slower refresh rate for real LLM workflows
    st.rerun()

