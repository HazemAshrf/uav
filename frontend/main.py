"""Main Streamlit application for Static Agent Dashboard."""

import streamlit as st
import sys
import os
from pathlib import Path

<<<<<<< HEAD
# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

# Configure page
st.set_page_config(
    page_title="Static Agent Dashboard",
    page_icon="🤖",
=======
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
>>>>>>> ae778f3 (second commit)
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_file = Path(__file__).parent / "assets" / "styles.css"
if css_file.exists():
<<<<<<< HEAD
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
=======
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
>>>>>>> ae778f3 (second commit)
## Welcome to the Static Agent Dashboard

This dashboard provides a **read-only** view of the UAV design agent system. Unlike the dynamic version, this system uses a predefined set of agents with static configurations.

### Available Pages:

<<<<<<< HEAD
#### 🤖 Agent Details
=======
#### {CrossPlatformEmoji.get("🤖")} Agent Details
>>>>>>> ae778f3 (second commit)
- View all static agents and their configurations
- Inspect agent roles, tools, and communication permissions
- **No editing capabilities** - agents are statically defined

<<<<<<< HEAD
#### 💬 Conversations  
=======
#### {CrossPlatformEmoji.get("💬")} Conversations  
>>>>>>> ae778f3 (second commit)
- Monitor real-time agent-to-agent communications
- View chat histories between agents
- Track message flow and timing

<<<<<<< HEAD
#### 📊 Workflow Status
=======
#### {CrossPlatformEmoji.get("📊")} Workflow Status
>>>>>>> ae778f3 (second commit)
- Monitor workflow execution progress
- View iteration summaries and agent outputs
- Track system stability and completion status

---

### Static Agent System Features:

<<<<<<< HEAD
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
=======
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
>>>>>>> ae778f3 (second commit)
    st.info("""
    **Mode**: Static Agent System
    **Agents**: 6 predefined agents
    **Communication**: Chat-based
    **Memory**: Checkpointing enabled
    """)
    
<<<<<<< HEAD
    st.markdown("### 📚 Static Agents")
    agents = [
        "🎯 Mission Planner",
        "🌊 Aerodynamics", 
        "🚀 Propulsion",
        "🏗️ Structures", 
        "🏭 Manufacturing",
        "👥 Coordinator"
=======
    st.markdown(f"### {CrossPlatformEmoji.get('📚')} Static Agents")
    agents = [
        f"{CrossPlatformEmoji.get('🎯')} Mission Planner",
        f"{CrossPlatformEmoji.get('🌊')} Aerodynamics", 
        f"{CrossPlatformEmoji.get('🚀')} Propulsion",
        f"{CrossPlatformEmoji.get('🏗️')} Structures", 
        f"{CrossPlatformEmoji.get('🏭')} Manufacturing",
        f"{CrossPlatformEmoji.get('👥')} Coordinator"
>>>>>>> ae778f3 (second commit)
    ]
    
    for agent in agents:
        st.markdown(f"• {agent}")