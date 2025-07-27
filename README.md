# Static Agent Dashboard

A **read-only** multi-agent system for UAV design with chat-based communication and checkpointing capabilities.

## Overview

This is the static version of the dynamic agent dashboard, implementing the same core functionality from `uav_design_system/langgraph/` but with two key modifications:

1. **Chat-based Communication**: Replaces the mailbox system with structured chat threads between agents
2. **Checkpointing**: Uses LangGraph's built-in checkpointing for memory management instead of custom memory systems

## Key Features

### ✅ Static Agent System
- **6 Predefined Agents**: Mission Planner, Aerodynamics, Propulsion, Structures, Manufacturing, Coordinator
- **Fixed Configuration**: No runtime agent modification or creation
- **Predefined Communication Rules**: Static agent-to-agent communication permissions

### 💬 Chat-Based Communication
- **Structured Conversations**: Agent-to-agent communication via chat threads
- **Message Types**: Communication, task assignment, error messages, system notifications
- **Real-time Monitoring**: Live view of agent conversations and message flow

### 🔄 Checkpointing & Memory
- **Built-in Persistence**: Uses LangGraph's MemorySaver for state persistence
- **Workflow Resume**: Ability to resume workflows from any checkpoint
- **Iteration Tracking**: Complete history of workflow execution states

### 🌐 Read-Only Web Interface
- **Agent Details**: View agent configurations, roles, and communication permissions
- **Live Conversations**: Monitor real-time agent communications
- **Workflow Status**: Track execution progress and system metrics
- **No Editing**: Pure monitoring interface without modification capabilities

## Architecture

```
static_agent_dashboard/
├── backend/
│   ├── agents/           # Static base agent class
│   ├── langgraph/        # Modified workflow with chat system
│   ├── config.py         # System configuration
│   ├── pydantic_models.py # Data models
│   └── ...
├── agents/               # Individual agent implementations
├── frontend/
│   ├── main.py          # Streamlit main app
│   ├── pages/           # Individual page components
│   └── assets/          # CSS and static files
├── main.py              # Main entry point
└── README.md
```

## Installation

1. **Clone and navigate:**
```bash
cd /path/to/uav_full/static_agent_dashboard
```

2. **Install uv (if not already installed):**
```bash
pip install uv
```

3. **Sync dependencies with uv:**
```bash
uv sync
```

4. **Set up environment variables:**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

## Usage

### Using UV (Recommended)

#### Run Both Workflow and Frontend
```bash
uv run python main.py --mode both
# OR use the convenience script
python run_system.py --both
# OR use the bash script
./run.sh --both
```

#### Run Only Workflow Backend
```bash
uv run python main.py --mode workflow
# OR
python run_system.py --workflow
```

#### Run Only Frontend (for existing data)
```bash
uv run python main.py --mode frontend
# OR  
python run_system.py --frontend
```

### Using Traditional Python (Alternative)
```bash
pip install -r requirements.txt
python main.py --mode both
```

### Access Web Interface
Open your browser to: `http://localhost:8501`

## Differences from Dynamic System

| Feature | Dynamic System | Static System |
|---------|----------------|---------------|
| **Agent Management** | Add/edit/remove agents via UI | Fixed set of 6 agents |
| **Communication** | Mailbox-based messaging | Chat-based conversations |
| **Memory System** | Custom memory implementation | LangGraph checkpointing |
| **UI Capabilities** | Full CRUD operations | Read-only monitoring |
| **Agent Configuration** | Runtime file uploads | Predefined configurations |
| **State Modification** | Dynamic agent injection | Static workflow execution |

## System Components

### Backend (`backend/`)
- **`langgraph/state.py`**: Chat-based global state management
- **`langgraph/workflow.py`**: Workflow with checkpointing support
- **`agents/base_agent.py`**: Static base agent class with chat integration

### Agents (`agents/`)
- **Coordinator**: Task assignment and project oversight
- **Mission Planner**: Requirements analysis and MTOW calculation
- **Aerodynamics**: Wing design and aerodynamic analysis
- **Propulsion**: Motor and propeller selection
- **Structures**: Airframe design and structural analysis
- **Manufacturing**: Production planning and cost analysis

### Frontend (`frontend/`)
- **Agent Details**: Read-only agent configuration viewer
- **Conversations**: Real-time chat monitoring interface
- **Workflow Status**: Execution progress and system metrics

## Configuration

### Static Agent Configuration
Agents are configured in `backend/langgraph/state.py` with predefined:
- Communication permissions
- Roles and responsibilities
- System prompts and tools

### Workflow Settings
- **Max Iterations**: 10 (configurable)
- **Stability Threshold**: 3 iterations
- **Checkpointing**: Enabled with MemorySaver
- **Thread Management**: Automatic thread ID generation

## Monitoring Capabilities

### Real-time Features
- ✅ Live agent conversation monitoring
- ✅ Workflow execution progress tracking
- ✅ System performance metrics
- ✅ Message flow visualization
- ✅ Iteration history and summaries

### System Metrics
- Agent execution status
- Communication activity
- Workflow completion percentage
- System stability indicators
- Error tracking and reporting

## Development

### Adding New Static Agents
1. Define agent in `agents/` directory
2. Inherit from `StaticBaseAgent`
3. Add to static configuration in `state.py`
4. Update communication rules

### Extending UI Components
1. Add new pages to `frontend/pages/`
2. Follow Streamlit multi-page structure
3. Use consistent styling from `assets/styles.css`

## Limitations

- **No Runtime Agent Creation**: Agents must be predefined in code
- **Read-Only Interface**: No UI-based system modifications
- **Static Communication Rules**: Agent permissions cannot be changed at runtime
- **Fixed Tools**: Agent tool sets are predetermined

## Support

This is a demonstration system showcasing chat-based multi-agent communication with checkpointing. For production use, consider:

- Database persistence for workflow states  
- Authentication and authorization
- Scalable agent execution environment
- Advanced monitoring and alerting
- API endpoints for external integration

---

**Note**: This system is designed as a monitoring and analysis tool for multi-agent workflows, not for interactive agent management.