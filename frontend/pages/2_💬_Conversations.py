"""Conversations page - Live view of agent communications."""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
import time

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.append(str(backend_path))

from langgraph.state import StaticGlobalState

# Page configuration
st.set_page_config(
    page_title="Conversations - Static Agent Dashboard",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_file = Path(__file__).parent.parent / "assets" / "styles.css"
if css_file.exists():
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Add ChatAI-style CSS
st.markdown("""
<style>
    /* ChatAI-inspired styling */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    /* ChatAI Widget Chat Messages - EXACT COPY */
    .chat-messages {
        flex: 1;
        padding: 16px;
        overflow-y: auto;
        background: #E5DDD5; /* WhatsApp background color */
        border-radius: 10px;
        min-height: 400px;
        max-height: 600px;
    }

    .message {
        margin-bottom: 12px;
        display: flex;
        flex-direction: column;
    }

    /* User messages - right side, green */
    .user-message {
        align-items: flex-end;
    }

    .user-message .message-bubble {
        background: #DCF8C6; /* WhatsApp green */
        border-radius: 18px 18px 6px 18px;
        margin-left: 60px;
    }

    /* AI messages - left side, white */
    .ai-message {
        align-items: flex-start;
    }

    .ai-message .message-bubble {
        background: #FFFFFF;
        border-radius: 18px 18px 18px 6px;
        margin-right: 60px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }

    /* Human agent messages - left side, blue */
    .agent-message {
        align-items: flex-start;
    }

    .agent-message .message-bubble {
        background: #E3F2FD; /* Light blue for human agents */
        border-radius: 18px 18px 18px 6px;
        margin-right: 60px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }

    .message-sender {
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 4px;
        padding: 0 4px;
    }

    .user-message .message-sender {
        color: #075E54;
        text-align: right;
    }

    .ai-message .message-sender {
        color: #1976D2;
    }

    .agent-message .message-sender {
        color: #1565C0;
    }

    .message-bubble {
        padding: 8px 12px;
        max-width: 100%;
        word-wrap: break-word;
        position: relative;
    }

    .message-content {
        font-size: 14px;
        line-height: 1.4;
        margin: 0;
        color: #303030;
    }

    .message-time {
        font-size: 11px;
        color: #999;
        margin-top: 4px;
        text-align: right;
        opacity: 0.8;
    }
    
    /* Conversation list styling */
    .conversation-item {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: all 0.3s ease;
    }
    
    .conversation-item:hover {
        background: rgba(255, 255, 255, 0.95);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* Header styling */
    .main-header {
        background: rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        color: white;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.8);
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def format_timestamp(timestamp):
    """Format timestamp for display."""
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Unknown"

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

# Header
st.markdown("""
<div class="main-header">
    <div class="header-content">
        <h1>💬 Agent Conversations</h1>
        <p>Monitor real-time agent-to-agent communications</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize or get state from session
if 'workflow_state' not in st.session_state:
    st.session_state.workflow_state = StaticGlobalState()

# Check if the state object has the reset_chats method, if not recreate it
# BUT respect the protection flag for completed workflows
should_recreate = not hasattr(st.session_state.workflow_state, 'reset_chats')

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

state = st.session_state.workflow_state

# Debug: Check if data is preserved after workflow completion
workflow_completed = st.session_state.get('workflow_completed', False)
if workflow_completed and state.chats:
    print(f"🔍 DEBUG: Completed workflow has {len(state.chats)} chats preserved")
elif workflow_completed:
    print("🔍 DEBUG: Completed workflow but no chats found in state")

# Check if workflow is running and get live data from progress file
workflow_running = st.session_state.get('workflow_running', False)
live_state_data = None

if workflow_running:
    try:
        workflow_thread_id = st.session_state.get('workflow_thread_id', 'static_uav_design')
        temp_state = StaticGlobalState(thread_id=workflow_thread_id)
        live_state_data = temp_state.read_progress_file()
    except Exception as e:
        print(f"❌ Error reading live state: {e}")
        live_state_data = None

# Sidebar for settings and filters
with st.sidebar:
    st.markdown("### ⚙️ Display Settings")
    
    # Message filters
    st.markdown("### 🔍 Message Filters")
    
    show_system_messages = st.checkbox("Show system messages", value=True)
    show_error_messages = st.checkbox("Show error messages", value=True)
    
    # Agent filter
    all_agents = list(state.static_agents.keys())
    selected_agents = st.multiselect(
        "Filter by agents:",
        all_agents,
        default=all_agents,
        format_func=get_agent_display_name
    )
    
    # Message limit
    max_messages = st.slider("Max messages per conversation", 10, 100, 25)
    
    # Manual refresh
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()

# Show workflow status and live data indicator
if workflow_running and live_state_data:
    st.info(f"""
    🔄 **Live Data Mode**: Displaying real-time conversation data
    
    **Current Status**: {live_state_data.get('status', 'running')}
    **Iteration**: {live_state_data.get('current_iteration', 0)}/{live_state_data.get('max_iterations', 10)}
    **Total Messages**: {live_state_data.get('total_messages', 0)}
    **Total Chats**: {live_state_data.get('total_chats', 0)}
    **Total Tools Used**: {live_state_data.get('total_tools_used', 0)}
    """)
elif workflow_running:
    st.warning("🔄 Workflow is running but live data not available yet...")
else:
    st.info("⭕ Workflow inactive - showing stored conversation data")

# Main content - use live chat data if available
live_chats_data = {}
if workflow_running and live_state_data and 'full_chats' in live_state_data:
    # Use full live chat data from workflow
    live_chats_data = live_state_data['full_chats']
    chat_summaries = live_state_data.get('chat_summaries', [])
    if chat_summaries:
        st.success(f"🔄 Displaying {len(chat_summaries)} live conversations from running workflow")
elif workflow_running and live_state_data and 'chat_summaries' in live_state_data:
    # Use live chat summaries from workflow (fallback)
    chat_summaries = live_state_data['chat_summaries']
    if chat_summaries:
        st.success(f"🔄 Displaying {len(chat_summaries)} live conversations from running workflow")
else:
    # Use session state for non-running workflows
    chat_summaries = state.get_all_chat_summaries()

if not chat_summaries:
    st.markdown("""
    <div class="info-section">
        <h3>👋 Welcome to Agent Conversations</h3>
        <p>No active conversations yet. Conversations will appear here when agents start communicating.</p>
        <p>In a live system, you would see:</p>
        <ul>
            <li>🔍 <strong>Real-time chats</strong> between agent pairs</li>
            <li>📊 <strong>Message flow</strong> and communication patterns</li>
            <li>🐛 <strong>Debug information</strong> for agent interactions</li>
            <li>📈 <strong>Communication analytics</strong> and timing</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
else:
    # Display metrics
    st.markdown("## 📊 Communication Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Active Conversations", len(chat_summaries))
    
    with col2:
        total_messages = sum(summary["message_count"] for summary in chat_summaries)
        st.metric("Total Messages", total_messages)
    
    with col3:
        active_participants = set()
        for summary in chat_summaries:
            active_participants.update(summary["participants"])
        st.metric("Active Agents", len(active_participants))
    
    with col4:
        # Get tool counts from state
        total_tools_used = state.get_total_tool_calls()
        st.metric("Tools Used", total_tools_used)
    
    with col5:
        if chat_summaries:
            last_activity = max((s.get("last_activity", 0) for s in chat_summaries), default=0)
            st.metric("Last Activity", format_timestamp(last_activity))
    
    st.markdown("---")
    
    # Tool usage breakdown
    tool_counts = state.get_current_tool_counts()
    if tool_counts and any(count > 0 for count in tool_counts.values()):
        st.markdown("## 🔧 Tool Usage Breakdown")
        
        tool_cols = st.columns(len([t for t in tool_counts.items() if t[1] > 0]))
        col_idx = 0
        
        for tool_name, count in tool_counts.items():
            if count > 0:
                with tool_cols[col_idx]:
                    # Clean up tool name for display
                    display_name = tool_name.replace('_', ' ').title()
                    st.metric(display_name, count)
                col_idx += 1
        
        st.markdown("---")
    
    # Display conversations
    st.markdown("## 💬 Active Conversations")
    
    for i, summary in enumerate(chat_summaries):
        participants = summary["participants"]
        
        # Filter by selected agents
        if not any(agent in selected_agents for agent in participants):
            continue
        
        # Get display names
        display_participants = [get_agent_display_name(p) for p in participants]
        
        # Handle live data vs session data differently
        if workflow_running and live_chats_data and summary['chat_key'] in live_chats_data:
            # Live data with full messages available
            live_chat_data = live_chats_data[summary['chat_key']]
            latest_preview = f" | Live: {len(live_chat_data['messages'])} msgs"
            
            with st.expander(
                f"💬 {' ↔️ '.join(display_participants)} ({summary['message_count']} messages){latest_preview}",
                expanded=False
            ):
                st.success("🔄 **Live conversation data** - Real-time messages")
                
                # Conversation metadata
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Participants:** {', '.join(display_participants)}")
                    st.markdown(f"**Chat Type:** {live_chat_data.get('chat_type', 'Unknown').replace('_', ' ').title()}")
                    st.markdown(f"**Total Messages:** {len(live_chat_data['messages'])}")
                
                with col2:
                    if live_chat_data.get('last_activity'):
                        st.markdown(f"**Last Activity:** {format_timestamp(live_chat_data['last_activity'])}")
                
                st.markdown("**Live Messages:**")
                
                # Get and filter live messages
                live_messages = live_chat_data['messages'][-max_messages:] if len(live_chat_data['messages']) > max_messages else live_chat_data['messages']
                
                if len(live_chat_data['messages']) > max_messages:
                    st.info(f"Showing last {max_messages} messages (out of {len(live_chat_data['messages'])} total)")
                
                # Build complete WhatsApp chat as single HTML block for live messages
                messages_html_parts = []
                
                for msg_data in live_messages:
                    # Apply filters
                    if msg_data['message_type'] == "system" and not show_system_messages:
                        continue
                    if msg_data['message_type'] == "error" and not show_error_messages:
                        continue
                    
                    # Get display info
                    sender_display = get_agent_display_name(msg_data['from_agent'])
                    is_left_side = participants[0] == msg_data['from_agent']
                    
                    # Clean message content
                    clean_content = msg_data['content'].replace('<', '&lt;').replace('>', '&gt;')
                    
                    # Format time
                    try:
                        time_str = format_timestamp(msg_data['timestamp']).split()[1]
                    except:
                        time_str = "00:00:00"
                    
                    # Determine message class
                    message_class = "ai-message" if is_left_side else "user-message"
                    
                    # Build individual message HTML
                    message_html = f"""
                    <div class="message {message_class}">
                        <div class="message-sender">{sender_display}</div>
                        <div class="message-bubble">
                            <div class="message-content">{clean_content}</div>
                            <div class="message-time">Iter: {msg_data['iteration']} | {time_str}</div>
                        </div>
                    </div>"""
                    
                    messages_html_parts.append(message_html)
                
                # Combine all messages in WhatsApp container
                if messages_html_parts:
                    complete_chat_html = f"""
                    <div class="chat-messages">
                        {''.join(messages_html_parts)}
                    </div>
                    """
                    st.markdown(complete_chat_html, unsafe_allow_html=True)
                else:
                    st.info("No messages to display with current filters.")
                    
        elif workflow_running and live_state_data and 'chat_summaries' in live_state_data:
            # Live data - limited chat preview (fallback when full_chats not available)
            latest_preview = f" | {summary.get('chat_type', 'conversation').replace('_', ' ').title()}"
            
            with st.expander(
                f"💬 {' ↔️ '.join(display_participants)} ({summary['message_count']} messages){latest_preview}",
                expanded=False
            ):
                st.info("🔄 **Live conversation data** - Full message history available when workflow completes")
                st.markdown(f"**Participants:** {', '.join(display_participants)}")
                st.markdown(f"**Message Count:** {summary['message_count']}")
                st.markdown(f"**Chat Type:** {summary.get('chat_type', 'Unknown').replace('_', ' ').title()}")
                if summary.get('last_activity'):
                    st.markdown(f"**Last Activity:** {format_timestamp(summary['last_activity'])}")
        else:
            # Session data - full chat display
            chat = state.get_chat(participants[0], participants[1])
            if not chat:
                continue
            
            # Show latest message preview
            latest_msg = chat.messages[-1] if chat.messages else None
            latest_preview = ""
            if latest_msg:
                preview_text = latest_msg.content[:60] + "..." if len(latest_msg.content) > 60 else latest_msg.content
                latest_preview = f" | Latest: {preview_text}"
            
            with st.expander(
                f"💬 {' ↔️ '.join(display_participants)} ({summary['message_count']} messages){latest_preview}",
                expanded=False  # All conversations collapsed by default
            ):
                # Conversation metadata
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Participants:** {', '.join(display_participants)}")
                    st.markdown(f"**Chat Type:** {summary.get('chat_type', 'Unknown').replace('_', ' ').title()}")
                    st.markdown(f"**Total Messages:** {summary['message_count']}")
                
                with col2:
                    if summary.get("last_activity"):
                        st.markdown(f"**Last Activity:** {format_timestamp(summary['last_activity'])}")
                
                st.markdown("**Messages:**")
                
                # Get and filter messages
                messages = chat.messages[-max_messages:] if len(chat.messages) > max_messages else chat.messages
                
                if len(chat.messages) > max_messages:
                    st.info(f"Showing last {max_messages} messages (out of {len(chat.messages)} total)")
                
                # Build complete WhatsApp chat as single HTML block
                messages_html_parts = []
                
                for msg in messages:
                    # Apply filters
                    if msg.message_type == "system" and not show_system_messages:
                        continue
                    if msg.message_type == "error" and not show_error_messages:
                        continue
                    
                    # Get display info (clean content but don't escape HTML structure)
                    sender_display = get_agent_display_name(msg.from_agent)
                    is_left_side = participants[0] == msg.from_agent
                    
                    # Clean message content (remove any potential HTML tags in content)
                    clean_content = msg.content.replace('<', '&lt;').replace('>', '&gt;')
                    
                    # Format time
                    try:
                        time_str = format_timestamp(msg.timestamp).split()[1]
                    except:
                        time_str = "00:00:00"
                    
                    # Determine message class
                    message_class = "ai-message" if is_left_side else "user-message"
                    
                    # Build individual message HTML
                    message_html = f"""
                    <div class="message {message_class}">
                        <div class="message-sender">{sender_display}</div>
                        <div class="message-bubble">
                            <div class="message-content">{clean_content}</div>
                            <div class="message-time">Iter: {msg.iteration} | {time_str}</div>
                        </div>
                    </div>"""
                    
                    messages_html_parts.append(message_html)
                
                # Combine all messages in WhatsApp container
                if messages_html_parts:
                    complete_chat_html = f"""
                    <div class="chat-messages">
                        {''.join(messages_html_parts)}
                    </div>
                    """
                    st.markdown(complete_chat_html, unsafe_allow_html=True)
                else:
                    st.info("No messages to display with current filters.")

# Real-time updates section
st.markdown("---")
st.markdown("## 🔄 System Status")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📡 Connection Status")
    st.success("✅ Connected to agent system")
    st.info(f"🔄 Last updated: {datetime.now().strftime('%H:%M:%S')}")

with col2:
    st.markdown("### 📊 System Metrics")  
    progress_info = state.get_workflow_progress()
    st.markdown(f"**Current Iteration:** {progress_info['current_iteration']}")
    st.markdown(f"**Total Chats:** {progress_info['total_chats']}")
    st.markdown(f"**Total Messages:** {progress_info['total_messages']}")
    st.markdown(f"**Total Tools Used:** {state.get_total_tool_calls()}")

# Information panel
with st.sidebar:
    st.markdown("### 💡 Tips")
    st.info("""
    **Real-time Monitoring:**
    - Enable auto-refresh for live updates
    - Filter messages by agent or type
    - Expand conversations to see details
    
    **Message Types:**
    - Communication: Agent-to-agent info sharing
    - Task: Coordinator task assignments  
    - Error: System error messages
    - System: Internal system messages
    """)

# Live updates - automatically refresh when workflow is running
if st.session_state.get('workflow_running', False):
    time.sleep(0.8)  # Slightly faster refresh for conversations
    st.rerun()

