"""Pydantic models for agent outputs and communication."""

from typing import List
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    """Message from one agent to another."""
    to_agent: str = Field(description="Target agent to send message to")
    content: str = Field(description="Message content")


class MissionPlannerOutput(BaseModel):
    """Agent 1: Mission Planner output"""
    mtow: float = Field(description="Maximum Take-Off Weight in kg")
    range_km: float = Field(description="Mission range in kilometers")
    payload_kg: float = Field(description="Payload weight in kg")
    endurance_hours: float = Field(description="Flight endurance in hours")
    altitude_m: float = Field(description="Operating altitude in meters")
    messages: List[AgentMessage] = Field(default=[], description="Messages to send to other agents")
    iteration: int = Field(description="Current iteration number")


class AerodynamicsOutput(BaseModel):
    """Agent 2: Aerodynamics Engineer output"""
    wing_area_m2: float = Field(description="Wing area in square meters")
    aspect_ratio: float = Field(description="Wing aspect ratio")
    airfoil_type: str = Field(description="Selected airfoil type")
    lift_to_drag_ratio: float = Field(description="Lift-to-drag ratio")
    stall_speed_ms: float = Field(description="Stall speed in m/s")
    messages: List[AgentMessage] = Field(default=[], description="Messages to send to other agents")
    iteration: int = Field(description="Current iteration number")


class PropulsionOutput(BaseModel):
    """Agent 3: Propulsion Engineer output"""
    engine_power_kw: float = Field(description="Required engine power in kW")
    thrust_n: float = Field(description="Required thrust in Newtons")
    engine_type: str = Field(description="Engine type (electric/turbine/combustion)")
    fuel_consumption_rate: float = Field(description="Fuel/energy consumption rate")
    engine_weight_kg: float = Field(description="Engine weight in kg")
    messages: List[AgentMessage] = Field(default=[], description="Messages to send to other agents")
    iteration: int = Field(description="Current iteration number")


class StructuresOutput(BaseModel):
    """Agent 4: Structures Engineer output"""
    fuselage_length_m: float = Field(description="Fuselage length in meters")
    wing_spar_material: str = Field(description="Wing spar material")
    fuselage_material: str = Field(description="Fuselage material")
    safety_factor: float = Field(description="Structural safety factor")
    structural_weight_kg: float = Field(description="Total structural weight in kg")
    messages: List[AgentMessage] = Field(default=[], description="Messages to send to other agents")
    iteration: int = Field(description="Current iteration number")


class ManufacturingOutput(BaseModel):
    """Agent 5: Manufacturing & Cost Engineer output"""
    total_cost_usd: float = Field(description="Total manufacturing cost in USD")
    production_time_hours: float = Field(description="Production time in hours")
    material_cost_usd: float = Field(description="Material cost in USD")
    labor_cost_usd: float = Field(description="Labor cost in USD")
    feasibility_score: float = Field(description="Manufacturability score (0-1)")
    messages: List[AgentMessage] = Field(default=[], description="Messages to send to other agents")
    iteration: int = Field(description="Current iteration number")


class AgentTask(BaseModel):
    """Task assignment for an agent."""
    agent_name: str = Field(description="Name of the agent")
    task_description: str = Field(description="Specific task for this agent")


class CoordinatorOutput(BaseModel):
    """Coordinator output"""
    project_complete: bool = Field(description="Whether project is complete")
    completion_reason: str = Field(description="Detailed reason for completion/continuation")
    agent_tasks: List[AgentTask] = Field(default=[], description="Tasks for specific agents if continuing")
    messages: List[AgentMessage] = Field(default=[], description="Messages to send to specific agents")
    iteration: int = Field(description="Current iteration number")