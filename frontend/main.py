"""Main Streamlit application for Static Agent Dashboard."""

import streamlit as st
import sys
import os
from pathlib import Path

# Add backend to path using cross-platform utilities
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Import cross-platform utilities
from cross_platform_utils import (
    CrossPlatformEmoji, CrossPlatformPaths
)

# Configure page with cross-platform emoji
st.set_page_config(
    page_title="Static Agent Dashboard",
    page_icon=CrossPlatformEmoji.get("🤖"),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_file = Path(__file__).parent / "assets" / "styles.css"
if css_file.exists():
    with open(css_file, encoding='utf-8') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Main header with cross-platform emoji support
header_content = f"""
<div class="main-header">
    <div class="header-content">
        <h1>{CrossPlatformEmoji.get("🤖")} Static Agent Dashboard</h1>
        <p>Monitor static UAV design agents and their conversations</p>
    </div>
</div>
"""
st.markdown(header_content, unsafe_allow_html=True)

# Welcome content with cross-platform emojis
welcome_content = f"""
## Welcome to the Static Agent Dashboard

This dashboard provides a **read-only** view of the UAV design agent system. Unlike the dynamic version, this system uses a predefined set of agents with static configurations.

### Available Pages:

#### {CrossPlatformEmoji.get("🤖")} Agent Details
- View all static agents and their configurations
- Inspect agent roles, tools, and communication permissions
- **No editing capabilities** - agents are statically defined

#### {CrossPlatformEmoji.get("💬")} Conversations
- Monitor real-time agent-to-agent communications
- View chat histories between agents
- Track message flow and timing

#### {CrossPlatformEmoji.get("📊")} Workflow Status
- Monitor workflow execution progress
- View iteration summaries and agent outputs
- Track system stability and completion status

---

### Static Agent System Features:

{CrossPlatformEmoji.get("✅")} **Predefined Agents**: Mission Planner, Aerodynamics, Propulsion, Structures, Manufacturing, Coordinator

{CrossPlatformEmoji.get("✅")} **Chat-based Communication**: Replaces mailbox system with structured chats

{CrossPlatformEmoji.get("✅")} **Checkpointing**: Built-in state persistence and recovery

{CrossPlatformEmoji.get("✅")} **Real-time Monitoring**: Live updates on conversations and workflow progress

{CrossPlatformEmoji.get("⚠️")} **Read-only Interface**: No agent modification or creation capabilities"""
st.markdown(welcome_content)

st.markdown("---")
st.markdown("**Navigate using the sidebar to explore the system**")

# System status in sidebar
with st.sidebar:
    st.markdown(f"### {CrossPlatformEmoji.get('🔧')} System Information")
    st.info("""
    **Mode**: Static Agent System
    **Agents**: 6 predefined agents
    **Communication**: Chat-based
    **Memory**: Checkpointing enabled
    """)
    
    st.markdown(f"### {CrossPlatformEmoji.get('📚')} Static Agents")
    agents = [
        f"{CrossPlatformEmoji.get('🎯')} Mission Planner",
        f"{CrossPlatformEmoji.get('🌊')} Aerodynamics", 
        f"{CrossPlatformEmoji.get('🚀')} Propulsion",
        f"{CrossPlatformEmoji.get('🏗️')} Structures", 
        f"{CrossPlatformEmoji.get('🏭')} Manufacturing",
        f"{CrossPlatformEmoji.get('👥')} Coordinator"
    ]
    
    for agent in agents:
        st.markdown(f"• {agent}")