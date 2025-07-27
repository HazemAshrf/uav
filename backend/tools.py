"""Engineering tools for UAV design calculations."""

from typing import Dict, Any, List
from langchain_core.tools import tool

# Global tool call counters
tool_call_counts = {
    'weight_estimator': 0,
    'aerodynamic_calculator': 0,
    'power_requirement_calculator': 0,
    'cost_estimator': 0,
    'feasibility_checker': 0
}

def get_tool_counts() -> Dict[str, int]:
    """Get current tool call counts."""
    return tool_call_counts.copy()

def get_total_tool_calls() -> int:
    """Get total number of tool calls across all tools."""
    return sum(tool_call_counts.values())

def reset_tool_counts():
    """Reset all tool call counters to zero."""
    global tool_call_counts
    for tool_name in tool_call_counts:
        tool_call_counts[tool_name] = 0


@tool
def weight_estimator(length: float, width: float, material: str) -> float:
    """Tool 1: Estimate weight based on dimensions and material"""
    global tool_call_counts
    tool_call_counts['weight_estimator'] += 1
    
    material_density = {
        "aluminum": 2.7,
        "carbon_fiber": 1.6,
        "steel": 7.8,
        "plastic": 1.2
    }
    density = material_density.get(material.lower(), 2.0)
    return length * width * 0.1 * density


@tool
def aerodynamic_calculator(wing_area: float, velocity: float) -> Dict[str, float]:
    """Tool 2: Calculate aerodynamic properties"""
    global tool_call_counts
    tool_call_counts['aerodynamic_calculator'] += 1
    
    lift_coefficient = 1.2
    drag_coefficient = 0.05
    air_density = 1.225
    
    lift = 0.5 * air_density * velocity**2 * wing_area * lift_coefficient
    drag = 0.5 * air_density * velocity**2 * wing_area * drag_coefficient
    
    return {
        "lift_n": lift,
        "drag_n": drag,
        "lift_to_drag": lift / drag if drag > 0 else 0
    }


@tool
def power_requirement_calculator(weight: float, velocity: float) -> float:
    """Tool 3: Calculate power requirements"""
    global tool_call_counts
    tool_call_counts['power_requirement_calculator'] += 1
    
    return (weight * 9.81 * velocity) / 1000


@tool
def cost_estimator(weight: float, material: str, complexity: float) -> float:
    """Tool 4: Estimate manufacturing cost"""
    global tool_call_counts
    tool_call_counts['cost_estimator'] += 1
    
    material_cost_per_kg = {
        "aluminum": 5.0,
        "carbon_fiber": 50.0,
        "steel": 2.0,
        "plastic": 3.0
    }
    base_cost = material_cost_per_kg.get(material.lower(), 10.0)
    return weight * base_cost * complexity


@tool
def feasibility_checker(specifications: Dict[str, Any]) -> Dict[str, Any]:
    """Tool 5: Check design feasibility"""
    global tool_call_counts
    tool_call_counts['feasibility_checker'] += 1
    
    feasibility_score = 0.8
    issues = []
    
    if specifications.get("weight", 0) > 1000:
        feasibility_score -= 0.2
        issues.append("Weight too high")
    
    if specifications.get("cost", 0) > 100000:
        feasibility_score -= 0.3
        issues.append("Cost too high")
    
    return {
        "feasibility_score": max(0, feasibility_score),
        "issues": issues,
        "recommendations": ["Optimize weight", "Reduce cost"]
    }


# Tool collections for each agent
MISSION_PLANNER_TOOLS = [feasibility_checker]
AERODYNAMICS_TOOLS = [aerodynamic_calculator, weight_estimator]
PROPULSION_TOOLS = [power_requirement_calculator, weight_estimator]
STRUCTURES_TOOLS = [weight_estimator, feasibility_checker]
MANUFACTURING_TOOLS = [cost_estimator, feasibility_checker]

# All tools (for reference)
ALL_TOOLS = [
    weight_estimator,
    aerodynamic_calculator,
    power_requirement_calculator,
    cost_estimator,
    feasibility_checker
]