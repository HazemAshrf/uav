"""Agent Details page - Read-only view of static agents."""

import streamlit as st
import sys
import os
import time
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from langgraph.state import StaticGlobalState
from config import MODEL_NAME
from cross_platform_utils import CrossPlatformEmoji

# Page configuration
st.set_page_config(
    page_title="Agent Details - Static Agent Dashboard",
    page_icon=CrossPlatformEmoji.get("🤖"),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_file = Path(__file__).parent.parent / "assets" / "styles.css"
if css_file.exists():
    with open(css_file, encoding='utf-8') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <div class="header-content">
        <h1>🤖 Agent Details</h1>
        <p>View static agent configurations and capabilities</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize or get state from session (to check workflow status)
if 'workflow_state' not in st.session_state:
    st.session_state.workflow_state = StaticGlobalState()

# Check if the state object has the reset_chats method, if not recreate it
if not hasattr(st.session_state.workflow_state, 'reset_chats'):
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

state = st.session_state.workflow_state
workflow_running = st.session_state.get('workflow_running', False)

# Agent information with detailed descriptions
agent_details = {
    "coordinator": {
        "emoji": "👥",
        "display_name": "Project Coordinator",
        "description": "Orchestrates the overall UAV design process, assigns tasks to specialized agents, and makes final decisions on project completion.",
        "primary_functions": [
            "Task assignment and coordination",
            "Progress monitoring and evaluation", 
            "Decision making on project direction",
            "Quality assurance and validation"
        ],
        "key_tools": [
            "Task management utilities",
            "Progress tracking tools",
            "Decision analysis frameworks"
        ]
    },
    "mission_planner": {
        "emoji": "🎯",
        "display_name": "Mission Planning Specialist",
        "description": "Defines mission requirements, operational parameters, and establishes the Maximum Takeoff Weight (MTOW) for the UAV design.",
        "primary_functions": [
            "Mission requirement analysis",
            "Operational parameter definition",
            "MTOW calculation and optimization",
            "Performance criteria establishment"
        ],
        "key_tools": [
            "Mission analysis calculators",
            "Performance modeling tools",
            "Requirements validation utilities"
        ]
    },
    "aerodynamics": {
        "emoji": "🌊",
        "display_name": "Aerodynamics Engineer",
        "description": "Designs and optimizes the aerodynamic characteristics of the UAV including wing design, lift/drag calculations, and flight performance.",
        "primary_functions": [
            "Wing design and optimization",
            "Lift and drag coefficient calculation",
            "Airfoil selection and analysis",
            "Flight envelope determination"
        ],
        "key_tools": [
            "CFD analysis tools",
            "Aerodynamic calculators",
            "Wing design utilities",
            "Performance estimation tools"
        ]
    },
    "propulsion": {
        "emoji": "🚀", 
        "display_name": "Propulsion Engineer",
        "description": "Selects and sizes the propulsion system including motors, propellers, and power requirements to meet mission objectives.",
        "primary_functions": [
            "Motor selection and sizing",
            "Propeller design and optimization",
            "Power system analysis",
            "Efficiency optimization"
        ],
        "key_tools": [
            "Motor selection databases",
            "Propeller analysis tools",
            "Power calculation utilities",
            "Efficiency optimization algorithms"
        ]
    },
    "structures": {
        "emoji": "🏗️",
        "display_name": "Structures Engineer", 
        "description": "Designs the structural components of the UAV including airframe, materials selection, and structural analysis for safety and performance.",
        "primary_functions": [
            "Airframe design and analysis",
            "Material selection and optimization",
            "Structural load analysis", 
            "Weight optimization"
        ],
        "key_tools": [
            "FEA analysis tools",
            "Material property databases",
            "Structural design utilities",
            "Weight estimation tools"
        ]
    },
    "manufacturing": {
        "emoji": "🏭",
        "display_name": "Manufacturing Engineer",
        "description": "Develops manufacturing processes, cost analysis, and production planning to ensure the UAV design is manufacturable and cost-effective.",
        "primary_functions": [
            "Manufacturing process design",
            "Cost analysis and optimization",
            "Production planning",
            "Quality control planning"
        ],
        "key_tools": [
            "Cost estimation tools",
            "Manufacturing process databases",
            "Production planning utilities",
            "Quality assurance frameworks"
        ]
    }
}

# Display agents
st.markdown("## Static Agent Overview")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Active Agents")
    
    for agent_name, agent_config in state.static_agents.items():
        agent_info = agent_details.get(agent_name, {})
        
        with st.expander(f"{agent_info.get('emoji', '🤖')} {agent_info.get('display_name', agent_name.title())}", expanded=False):
            
            # Agent status - inactive by default, active only when workflow running
            if workflow_running and st.session_state.get('workflow_started', False):
                actual_status = "ACTIVE"
                status_class = "active"
            elif workflow_running:
                actual_status = "STARTING"
                status_class = "starting"
            else:
                actual_status = "INACTIVE"
                status_class = "inactive"
            
            st.markdown(f'<span class="agent-status {status_class}">{actual_status}</span>', unsafe_allow_html=True)
            
            # Description
            if agent_info.get("description"):
                st.markdown(f"**Description:** {agent_info['description']}")
            
            # Basic configuration including LLM
            st.markdown("**Configuration:**")
            st.json({
                "Name": agent_config.get("name", "N/A"),
                "Role": agent_config.get("role", "N/A"), 
                "LLM Model": MODEL_NAME,
                "Status": actual_status
            })
            
            # Communication permissions
            st.markdown("**Communication Permissions:**")
            comm_allowed = agent_config.get("communication_allowed", [])
            if comm_allowed:
                for comm_agent in comm_allowed:
                    comm_info = agent_details.get(comm_agent, {})
                    st.markdown(f"• {comm_info.get('emoji', '🤖')} {comm_info.get('display_name', comm_agent.title())}")
            else:
                st.markdown("• No communication permissions defined")
            
            # Primary functions
            if agent_info.get("primary_functions"):
                st.markdown("**Primary Functions:**")
                for func in agent_info["primary_functions"]:
                    st.markdown(f"• {func}")
            
            # Key tools (static information)
            if agent_info.get("key_tools"):
                st.markdown("**Available Tools:**")
                for tool in agent_info["key_tools"]:
                    st.markdown(f"• {tool}")

with col2:
    st.markdown("### System Statistics")
    
    # Agent count metrics
    total_agents = len(state.static_agents)
    active_agents = len([a for a in state.static_agents.values() if a.get("status") == "active"])
    
    st.metric("Total Agents", total_agents)
    st.metric("Active Agents", active_agents)
    st.metric("Communication Links", sum(len(a.get("communication_allowed", [])) for a in state.static_agents.values()))
    
    # Agent categories
    st.markdown("### Agent Categories")
    categories = {
        "Coordination": ["coordinator"],
        "Planning": ["mission_planner"],
        "Engineering": ["aerodynamics", "propulsion", "structures"],
        "Production": ["manufacturing"]
    }
    
    for category, agents in categories.items():
        count = len([a for a in agents if a in state.static_agents])
        st.markdown(f"**{category}:** {count} agent{'s' if count != 1 else ''}")

# Communication matrix
st.markdown("---")
st.markdown("## Agent Communication Matrix")

st.markdown("This matrix shows which agents can communicate with each other:")

# Create communication matrix
agents = list(state.static_agents.keys())
matrix_data = []

for from_agent in agents:
    row = [from_agent]
    comm_allowed = state.static_agents[from_agent].get("communication_allowed", [])
    
    for to_agent in agents:
        if from_agent == to_agent:
            row.append("—")
        elif to_agent in comm_allowed:
            row.append("✅")
        else:
            row.append("❌")
    
    matrix_data.append(row)

# Display as table
import pandas as pd
df = pd.DataFrame(matrix_data, columns=["From \\ To"] + [agent_details.get(a, {}).get('display_name', a.title()) for a in agents])
st.dataframe(df, use_container_width=True)

# Legend
st.markdown("""
**Legend:**
- ✅ Communication allowed
- ❌ Communication not allowed  
- — Same agent
""")

# System information
with st.sidebar:
    st.markdown("### 📊 System Information")
    
    st.info(f"""
    **Total Agents:** {total_agents}
    **Active Agents:** {active_agents}
    **System Mode:** Static (Read-only)
    **Memory System:** Chat-based with checkpointing
    """)
    
    st.markdown("### ⚠️ Important Notes")
    st.warning("""
    This is a **static agent system**. Agent configurations cannot be modified through this interface.
    
    All agents are predefined with fixed:
    - Roles and responsibilities
    - Communication permissions
    - Tool access
    - System prompts
    """)
    
    st.markdown("### 🔗 Quick Navigation")
    st.markdown("""
    - **💬 Conversations**: View agent communications
    - **📊 Workflow Status**: Monitor execution progress
    """)

# Live updates - automatically refresh when workflow is running
if workflow_running:
    time.sleep(0.5)  # Brief pause to avoid overwhelming the system
    st.rerun()