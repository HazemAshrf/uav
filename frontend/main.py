"""Main Streamlit application for Static Agent Dashboard."""

import streamlit as st
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

# Configure page
st.set_page_config(
    page_title="Static Agent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_file = Path(__file__).parent / "assets" / "styles.css"
if css_file.exists():
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <div class="header-content">
        <h1>🤖 Static Agent Dashboard</h1>
        <p>Monitor static UAV design agents and their conversations</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Welcome content
st.markdown("""
## Welcome to the Static Agent Dashboard

This dashboard provides a **read-only** view of the UAV design agent system. Unlike the dynamic version, this system uses a predefined set of agents with static configurations.

### Available Pages:

#### 🤖 Agent Details
- View all static agents and their configurations
- Inspect agent roles, tools, and communication permissions
- **No editing capabilities** - agents are statically defined

#### 💬 Conversations  
- Monitor real-time agent-to-agent communications
- View chat histories between agents
- Track message flow and timing

#### 📊 Workflow Status
- Monitor workflow execution progress
- View iteration summaries and agent outputs
- Track system stability and completion status

---

### Static Agent System Features:

✅ **Predefined Agents**: Mission Planner, Aerodynamics, Propulsion, Structures, Manufacturing, Coordinator

✅ **Chat-based Communication**: Replaces mailbox system with structured chats

✅ **Checkpointing**: Built-in state persistence and recovery

✅ **Real-time Monitoring**: Live updates on conversations and workflow progress

⚠️ **Read-only Interface**: No agent modification or creation capabilities

---

**Navigate using the sidebar to explore the system →**
""")

# System status in sidebar
with st.sidebar:
    st.markdown("### 🔧 System Information")
    st.info("""
    **Mode**: Static Agent System
    **Agents**: 6 predefined agents
    **Communication**: Chat-based
    **Memory**: Checkpointing enabled
    """)
    
    st.markdown("### 📚 Static Agents")
    agents = [
        "🎯 Mission Planner",
        "🌊 Aerodynamics", 
        "🚀 Propulsion",
        "🏗️ Structures", 
        "🏭 Manufacturing",
        "👥 Coordinator"
    ]
    
    for agent in agents:
        st.markdown(f"• {agent}")