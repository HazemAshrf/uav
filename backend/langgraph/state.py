"""Static global state with chat-based communication and checkpointing."""

import time
import threading
import json
import os
import tempfile
from typing import Dict, List, Any, Optional, Callable
from pydantic import BaseModel, Field, ConfigDict
from dataclasses import dataclass

# Import agent output models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pydantic_models import (
    MissionPlannerOutput, AerodynamicsOutput, PropulsionOutput,
    StructuresOutput, ManufacturingOutput, CoordinatorOutput
)


@dataclass
class ChatMessage:
    """Individual chat message between agents."""
    id: str
    from_agent: str
    to_agent: str
    content: str
    timestamp: float
    iteration: int
    message_type: str = "communication"  # communication, task, error, etc.
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AgentChat(BaseModel):
    """Chat thread between two agents."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    participants: List[str] = Field(default_factory=list)
    messages: List[ChatMessage] = Field(default_factory=list)
    last_activity: Optional[float] = None
    chat_type: str = "agent_to_agent"  # agent_to_agent, coordinator_to_agent
    
    def add_message(self, message: ChatMessage):
        """Add message to chat thread."""
        self.messages.append(message)
        self.last_activity = message.timestamp
        
    def get_messages_for_iteration(self, iteration: int) -> List[ChatMessage]:
        """Get messages for specific iteration."""
        return [msg for msg in self.messages if msg.iteration == iteration]
    
    def get_recent_messages(self, limit: int = 10) -> List[ChatMessage]:
        """Get most recent messages."""
        return sorted(self.messages, key=lambda x: x.timestamp)[-limit:]
    
    def get_messages_from_agent(self, agent_name: str) -> List[ChatMessage]:
        """Get all messages from a specific agent."""
        return [msg for msg in self.messages if msg.from_agent == agent_name]
    
    def get_messages_to_agent(self, agent_name: str) -> List[ChatMessage]:
        """Get all messages to a specific agent."""
        return [msg for msg in self.messages if msg.to_agent == agent_name]


class StaticGlobalState(BaseModel):
    """Static global state with predefined agents and chat-based communication."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Static agent outputs by iteration (same structure as original)
    mission_planner_outputs: Dict[int, MissionPlannerOutput] = Field(default_factory=dict)
    aerodynamics_outputs: Dict[int, AerodynamicsOutput] = Field(default_factory=dict)
    propulsion_outputs: Dict[int, PropulsionOutput] = Field(default_factory=dict)
    structures_outputs: Dict[int, StructuresOutput] = Field(default_factory=dict)
    manufacturing_outputs: Dict[int, ManufacturingOutput] = Field(default_factory=dict)
    coordinator_outputs: Dict[int, CoordinatorOutput] = Field(default_factory=dict)
    
    # Chat system replacing mailboxes
    chats: Dict[str, AgentChat] = Field(default_factory=lambda: {})
    
    # Static agent registry (predefined agents)
    static_agents: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "coordinator": {
            "name": "coordinator",
            "role": "Project Coordinator",
            "status": "active",
            "communication_allowed": ["mission_planner", "aerodynamics", "propulsion", "structures", "manufacturing"]
        },
        "mission_planner": {
            "name": "mission_planner", 
            "role": "Mission Planning Specialist",
            "status": "active",
            "communication_allowed": ["coordinator", "aerodynamics", "propulsion", "structures"]
        },
        "aerodynamics": {
            "name": "aerodynamics",
            "role": "Aerodynamics Engineer", 
            "status": "active",
            "communication_allowed": ["coordinator", "mission_planner", "propulsion", "structures"]
        },
        "propulsion": {
            "name": "propulsion",
            "role": "Propulsion Engineer",
            "status": "active", 
            "communication_allowed": ["coordinator", "mission_planner", "aerodynamics", "structures"]
        },
        "structures": {
            "name": "structures",
            "role": "Structures Engineer",
            "status": "active",
            "communication_allowed": ["coordinator", "mission_planner", "aerodynamics", "propulsion", "manufacturing"]
        },
        "manufacturing": {
            "name": "manufacturing",
            "role": "Manufacturing Engineer",
            "status": "active",
            "communication_allowed": ["coordinator", "structures"]
        }
    })
    
    # Iteration tracking (same as original)
    current_iteration: int = 0
    max_iterations: int = 10
    stability_threshold: int = 3
    last_update_iteration: Dict[str, int] = Field(default_factory=lambda: {
        "mission_planner": -1,
        "aerodynamics": -1,
        "propulsion": -1,
        "structures": -1,
        "manufacturing": -1
    })
    
    # Project status
    project_complete: bool = False
    user_requirements: str = ""
    
    # Checkpointing metadata
    thread_id: str = ""
    workflow_checkpoint_id: Optional[str] = None
    checkpoint_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Tools usage tracking
    tools_usage: Dict[str, int] = Field(default_factory=dict)
    
    # Progress tracking for UI (file-based, no locks to avoid serialization issues)
    workflow_status: str = "inactive"  # inactive, running, completed, error, waiting_for_user
    current_agent_processing: Optional[str] = None
    workflow_error: Optional[str] = None
    last_progress_update: float = Field(default_factory=time.time)
    
    # User decision handling for continue workflow
    waiting_for_user_decision: bool = False
    user_decision: Optional[str] = None  # "continue" or "start_new"
    additional_requirements: str = ""
    
    # Resume state tracking to prevent double increments
    is_resuming_workflow: bool = False
    
    def get_chat(self, agent1: str, agent2: str) -> Optional[AgentChat]:
        """Get chat between two agents."""
        chat_key = self._get_chat_key(agent1, agent2)
        return self.chats.get(chat_key)
    
    def create_chat(self, agent1: str, agent2: str) -> AgentChat:
        """Create new chat between two agents."""
        chat_key = self._get_chat_key(agent1, agent2)
        
        # Determine chat type
        chat_type = "coordinator_to_agent" if "coordinator" in [agent1, agent2] else "agent_to_agent"
        
        chat = AgentChat(
            participants=sorted([agent1, agent2]),
            chat_type=chat_type
        )
        self.chats[chat_key] = chat
        return chat
    
    def send_message(
        self, 
        from_agent: str, 
        to_agent: str, 
        content: str,
        message_type: str = "communication",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Send message between agents with communication rules."""
        # Check if communication is allowed
        if not self._can_communicate(from_agent, to_agent):
            print(f"⚠️ Warning: {from_agent} cannot send message to '{to_agent}' - not in allowed communication list")
            return False
        
        chat_key = self._get_chat_key(from_agent, to_agent)
        
        # Ensure chat exists
        if chat_key not in self.chats:
            self.create_chat(from_agent, to_agent)
        
        # Create message
        message = ChatMessage(
            id=f"{from_agent}_{to_agent}_{time.time()}",
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            timestamp=time.time(),
            iteration=self.current_iteration,
            message_type=message_type,
            metadata=metadata or {}
        )
        
        # Add to chat
        self.chats[chat_key].add_message(message)
        return True
    
    def get_agent_chats(self, agent_name: str) -> List[AgentChat]:
        """Get all chats involving a specific agent."""
        chats = []
        for chat in self.chats.values():
            if agent_name in chat.participants:
                chats.append(chat)
        return chats
    
    def get_messages_for_agent(self, agent_name: str, iteration: int = None) -> List[ChatMessage]:
        """Get messages for an agent, optionally filtered by iteration."""
        messages = []
        for chat in self.chats.values():
            if agent_name in chat.participants:
                chat_messages = chat.messages
                if iteration is not None:
                    chat_messages = [msg for msg in chat_messages if msg.iteration == iteration]
                messages.extend([msg for msg in chat_messages if msg.to_agent == agent_name])
        return sorted(messages, key=lambda x: x.timestamp)
    
    def get_messages_from_previous_iteration(self, agent_name: str) -> List[Dict[str, str]]:
        """Get messages for agent from previous iteration (compatibility with original)."""
        if self.current_iteration <= 0:
            return []
        
        prev_iteration = self.current_iteration - 1
        messages = self.get_messages_for_agent(agent_name, prev_iteration)
        return [{"from": msg.from_agent, "content": msg.content} for msg in messages]
    
    def _get_chat_key(self, agent1: str, agent2: str) -> str:
        """Generate consistent chat key for two agents."""
        return "_".join(sorted([agent1, agent2]))
    
    def _can_communicate(self, from_agent: str, to_agent: str) -> bool:
        """Check if from_agent can communicate with to_agent."""
        if from_agent not in self.static_agents:
            return False
        
        allowed = self.static_agents[from_agent].get("communication_allowed", [])
        return to_agent in allowed
    
    def get_all_chat_summaries(self) -> List[Dict[str, Any]]:
        """Get summary of all chats for UI display."""
        summaries = []
        for chat_key, chat in self.chats.items():
            if not chat.messages:
                continue
                
            summary = {
                "chat_key": chat_key,
                "participants": chat.participants,
                "message_count": len(chat.messages),
                "last_activity": chat.last_activity,
                "chat_type": chat.chat_type,
                "recent_messages": chat.get_recent_messages(5)
            }
            summaries.append(summary)
        
        # Sort by last activity
        summaries.sort(key=lambda x: x.get("last_activity", 0), reverse=True)
        return summaries
    
    def get_iteration_summary(self, iteration: int) -> Dict[str, Any]:
        """Get summary of what happened in a specific iteration."""
        summary = {
            "iteration": iteration,
            "agents_executed": [],
            "messages_sent": 0,
            "new_chats_created": 0
        }
        
        # Check which agents produced outputs
        agent_names = ["mission_planner", "aerodynamics", "propulsion", "structures", "manufacturing"]
        for agent_name in agent_names:
            outputs_dict = getattr(self, f"{agent_name}_outputs")
            if iteration in outputs_dict:
                summary["agents_executed"].append(agent_name)
        
        # Count messages sent in this iteration
        for chat in self.chats.values():
            iteration_messages = chat.get_messages_for_iteration(iteration)
            summary["messages_sent"] += len(iteration_messages)
        
        return summary
    
    def get_workflow_progress(self) -> Dict[str, Any]:
        """Get overall workflow progress information."""
        total_agents = len([agent for agent in self.static_agents.values() if agent["status"] == "active"])
        completed_agents = 0
        active_agents = 0
        
        # Count agents that have produced outputs in recent iterations
        recent_threshold = max(0, self.current_iteration - 2)
        for agent_name in self.static_agents.keys():
            if agent_name == "coordinator":
                continue
                
            last_update = self.last_update_iteration.get(agent_name, -1)
            if last_update >= recent_threshold:
                active_agents += 1
            
            outputs_dict = getattr(self, f"{agent_name}_outputs", {})
            if outputs_dict:
                completed_agents += 1
        
        progress_percentage = (completed_agents / total_agents * 100) if total_agents > 0 else 0
        
        # Ensure tools_usage exists for backward compatibility
        tools_usage = getattr(self, 'tools_usage', {})
        
        return {
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "total_agents": total_agents,
            "completed_agents": completed_agents,
            "active_agents": active_agents,
            "progress_percentage": progress_percentage,
            "is_stable": self._check_stability(),
            "is_complete": self.project_complete,
            "total_chats": len(self.chats),
            "total_messages": sum(len(chat.messages) for chat in self.chats.values()),
            "total_tools_used": sum(tools_usage.values()),
            "tools_breakdown": dict(tools_usage)
        }
    
    def _check_stability(self) -> bool:
        """Check if the system has reached stability."""
        if self.current_iteration < self.stability_threshold:
            return False
        
        # Check if any agent has updated within stability threshold
        for agent_name, last_update in self.last_update_iteration.items():
            if self.current_iteration - last_update < self.stability_threshold:
                return False
        
        return True
    
    def reset_chats(self):
        """Reset all chats and related communication data."""
        self.chats = {}
        # Safely reset tools_usage, creating it if it doesn't exist
        if hasattr(self, 'tools_usage'):
            self.tools_usage = {}
        else:
            self.tools_usage = {}
        print("🧹 All chats have been reset for new workflow run")
    
    def reset_chats_and_tools(self):
        """Reset all chats and tool counters for a completely fresh start."""
        self.reset_chats()
        # Reset tool counters in tools.py
        self.reset_tool_counts()
        print("🧹 All chats and tool counters have been reset for new workflow run")
    
    def increment_tool_usage(self, tool_name: str):
        """Increment usage count for a specific tool."""
        # Ensure tools_usage exists
        if not hasattr(self, 'tools_usage'):
            self.tools_usage = {}
        self.tools_usage[tool_name] = self.tools_usage.get(tool_name, 0) + 1
    
    def get_current_tool_counts(self) -> Dict[str, int]:
        """Get current tool call counts from tools.py."""
        try:
            import sys
            import os
            # Add backend to path
            backend_dir = os.path.dirname(os.path.dirname(__file__))
            if backend_dir not in sys.path:
                sys.path.append(backend_dir)
            
            from tools import get_tool_counts
            return get_tool_counts()
        except ImportError:
            print("❌ Warning: Could not import tool counts from tools.py")
            return {}
    
    def get_total_tool_calls(self) -> int:
        """Get total number of tool calls from tools.py."""
        try:
            import sys
            import os
            # Add backend to path
            backend_dir = os.path.dirname(os.path.dirname(__file__))
            if backend_dir not in sys.path:
                sys.path.append(backend_dir)
            
            from tools import get_total_tool_calls
            return get_total_tool_calls()
        except ImportError:
            print("❌ Warning: Could not import total tool calls from tools.py")
            return 0
    
    def reset_tool_counts(self):
        """Reset tool counters in tools.py for new workflow run."""
        try:
            import sys
            import os
            # Add backend to path
            backend_dir = os.path.dirname(os.path.dirname(__file__))
            if backend_dir not in sys.path:
                sys.path.append(backend_dir)
            
            from tools import reset_tool_counts
            reset_tool_counts()
            print("🧹 Tool counters have been reset")
        except ImportError:
            print("❌ Warning: Could not reset tool counts in tools.py")
    
    # Simple progress tracking methods (no locks to avoid serialization issues)
    def get_progress_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of current progress."""
        # Get tool counts - prefer state's tools_usage over importing from tools.py
        if hasattr(self, 'tools_usage') and self.tools_usage:
            current_tool_counts = self.tools_usage
            total_tools_used = sum(self.tools_usage.values())
        else:
            # Fallback to importing from tools.py
            current_tool_counts = self.get_current_tool_counts()
            total_tools_used = self.get_total_tool_calls()
        
        # Include full chat data with messages in progress data for UI
        chat_summaries_data = []
        full_chats_data = {}
        try:
            summaries = self.get_all_chat_summaries()
            for summary in summaries:
                # Basic summary data
                chat_data = {
                    "chat_key": summary["chat_key"],
                    "participants": summary["participants"],
                    "message_count": summary["message_count"],
                    "last_activity": summary.get("last_activity"),
                    "chat_type": summary.get("chat_type", "unknown")
                }
                chat_summaries_data.append(chat_data)
                
                # Full chat data with messages for live display
                chat_key = summary["chat_key"]
                chat = self.chats.get(chat_key)
                if chat and chat.messages:
                    # Serialize all messages
                    messages_data = []
                    for msg in chat.messages:
                        msg_data = {
                            "id": msg.id,
                            "from_agent": msg.from_agent,
                            "to_agent": msg.to_agent,
                            "content": msg.content,
                            "timestamp": msg.timestamp,
                            "iteration": msg.iteration,
                            "message_type": msg.message_type,
                            "metadata": msg.metadata or {}
                        }
                        messages_data.append(msg_data)
                    
                    full_chats_data[chat_key] = {
                        "participants": chat.participants,
                        "messages": messages_data,
                        "last_activity": chat.last_activity,
                        "chat_type": chat.chat_type
                    }
        except Exception as e:
            print(f"❌ Warning: Could not serialize chat data: {e}")
            chat_summaries_data = []
            full_chats_data = {}
        
        return {
            "status": getattr(self, 'workflow_status', 'inactive'),
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "current_agent": getattr(self, 'current_agent_processing', None),
            "project_complete": self.project_complete,
            "error": getattr(self, 'workflow_error', None),
            "last_update": getattr(self, 'last_progress_update', time.time()),
            "progress_percent": (self.current_iteration / self.max_iterations * 100) if self.max_iterations > 0 else 0,
            "tools_usage": current_tool_counts,
            "total_tools_used": total_tools_used,
            "total_chats": len(getattr(self, 'chats', {})),
            "total_messages": sum(len(chat.messages) for chat in getattr(self, 'chats', {}).values()),
            "last_update_iteration": dict(getattr(self, 'last_update_iteration', {})),
            "chat_summaries": chat_summaries_data,
            "full_chats": full_chats_data
        }
    
    # File-based progress tracking for background threads
    def get_progress_file_path(self) -> str:
        """Get the file path for progress tracking."""
        return os.path.join(tempfile.gettempdir(), f"workflow_progress_{self.thread_id}.json")
    
    def write_progress_file(self):
        """Write current progress to file for UI polling with ALL metrics."""
        import fcntl
        import tempfile
        
        try:
            # Get comprehensive progress data
            progress_data = self.get_progress_snapshot()
            
            # Add file-specific data
            progress_data.update({
                "thread_id": self.thread_id,
                "user_requirements": self.user_requirements[:100] + "..." if len(self.user_requirements) > 100 else self.user_requirements,
                "timestamp": time.time()
            })
            
            file_path = self.get_progress_file_path()
            
            # Use atomic write to prevent corruption
            temp_path = file_path + '.tmp'
            with open(temp_path, 'w') as f:
                # Lock the file to prevent concurrent writes
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    json.dump(progress_data, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                except BlockingIOError:
                    # If we can't get the lock, skip this write to avoid corruption
                    print(f"⚠️ Progress file write skipped (locked by another process)")
                    return
                finally:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except:
                        pass
            
            # Atomic move to replace the original file
            if os.path.exists(temp_path):
                os.replace(temp_path, file_path)
                
        except Exception as e:
            print(f"❌ Error writing progress file: {e}")
            # Cleanup temp file if it exists
            temp_path = self.get_progress_file_path() + '.tmp'
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
    
    def read_progress_file(self) -> Dict[str, Any]:
        """Read progress from file with corruption handling."""
        import fcntl
        
        try:
            file_path = self.get_progress_file_path()
            if not os.path.exists(file_path):
                return {}
            
            # Try to read with file locking
            with open(file_path, 'r') as f:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                    content = f.read()
                    if not content.strip():
                        return {}
                    return json.loads(content)
                except BlockingIOError:
                    # File is locked, return empty to avoid blocking UI
                    print(f"⚠️ Progress file read skipped (locked by another process)")
                    return {}
                except json.JSONDecodeError as je:
                    print(f"⚠️ Progress file corrupted, attempting recovery: {je}")
                    # Try to recover by reading backup or returning empty
                    return {}
                finally:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except:
                        pass
                        
        except Exception as e:
            print(f"❌ Error reading progress file: {e}")
            # If file is corrupted, try to clean it up
            try:
                file_path = self.get_progress_file_path()
                if os.path.exists(file_path):
                    # Check if file is empty or corrupted
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if len(content) > 10000:  # File too large, might be corrupted
                            print(f"⚠️ Progress file too large ({len(content)} chars), cleaning up")
                            os.remove(file_path)
            except:
                pass
            return {}
    
    def sync_complete_data_to_state(self, target_state: 'StaticGlobalState'):
        """Sync all workflow data to target state before cleanup."""
        try:
            # Sync all agent outputs
            target_state.mission_planner_outputs = self.mission_planner_outputs
            target_state.aerodynamics_outputs = self.aerodynamics_outputs
            target_state.propulsion_outputs = self.propulsion_outputs
            target_state.structures_outputs = self.structures_outputs
            target_state.manufacturing_outputs = self.manufacturing_outputs
            target_state.coordinator_outputs = self.coordinator_outputs
            
            # Sync chats and communication
            target_state.chats = self.chats
            
            # Sync workflow state
            target_state.current_iteration = self.current_iteration
            target_state.max_iterations = self.max_iterations
            target_state.project_complete = self.project_complete
            target_state.last_update_iteration = self.last_update_iteration
            target_state.workflow_status = getattr(self, 'workflow_status', 'completed')
            
            # Sync tool counts (these should persist in tools.py but also in state)
            target_state.tools_usage = self.get_current_tool_counts()
            
            print("✅ Complete workflow data synced to session state")
            
        except Exception as e:
            print(f"❌ Error syncing workflow data: {e}")
    
    def cleanup_progress_file(self):
        """Clean up progress file when workflow completes."""
        try:
            file_path = self.get_progress_file_path()
            if os.path.exists(file_path):
                os.remove(file_path)
                print("🧹 Progress file cleaned up")
        except Exception as e:
            print(f"❌ Error cleaning up progress file: {e}")
    
    def update_progress_file(self, 
                            status: Optional[str] = None,
                            current_agent: Optional[str] = None, 
                            iteration: Optional[int] = None,
                            error: Optional[str] = None):
        """Thread-safe method to update workflow progress and write to file."""
        # Update internal state
        if status is not None:
            self.workflow_status = status
        if current_agent is not None:
            self.current_agent_processing = current_agent
        if iteration is not None:
            self.current_iteration = iteration
        if error is not None:
            self.workflow_error = error
            self.workflow_status = "error"
        
        self.last_progress_update = time.time()
        
        # Write to file for UI polling
        self.write_progress_file()