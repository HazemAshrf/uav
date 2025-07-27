"""Utility functions for the UAV design system."""

def print_final_design(state):
    """Print only the final design outputs."""
    print("=== FINAL UAV DESIGN ===")
    
    # Handle both dict and object state
    if isinstance(state, dict):
        mission_outputs = state.get("mission_planner_outputs", {})
        aero_outputs = state.get("aerodynamics_outputs", {})
        prop_outputs = state.get("propulsion_outputs", {})
        struct_outputs = state.get("structures_outputs", {})
        mfg_outputs = state.get("manufacturing_outputs", {})
    else:
        mission_outputs = state.mission_planner_outputs
        aero_outputs = state.aerodynamics_outputs
        prop_outputs = state.propulsion_outputs
        struct_outputs = state.structures_outputs
        mfg_outputs = state.manufacturing_outputs
    
    if mission_outputs:
        latest = mission_outputs[max(mission_outputs.keys())]
        print(f"Mission: MTOW={latest.mtow}kg, Range={latest.range_km}km, Payload={latest.payload_kg}kg")
    
    if aero_outputs:
        latest = aero_outputs[max(aero_outputs.keys())]
        print(f"Aerodynamics: Wing={latest.wing_area_m2}m², AR={latest.aspect_ratio}, L/D={latest.lift_to_drag_ratio}")
    
    if prop_outputs:
        latest = prop_outputs[max(prop_outputs.keys())]
        print(f"Propulsion: {latest.engine_power_kw}kW {latest.engine_type}, {latest.thrust_n}N thrust")
    
    if struct_outputs:
        latest = struct_outputs[max(struct_outputs.keys())]
        print(f"Structure: {latest.structural_weight_kg}kg {latest.wing_spar_material}")
    
    if mfg_outputs:
        latest = mfg_outputs[max(mfg_outputs.keys())]
        print(f"Manufacturing: ${latest.total_cost_usd}, Feasibility={latest.feasibility_score}")


def print_iteration_summary(state):
    """Print a summary of all iterations."""
    print("\n=== ITERATION SUMMARY ===")
    
    # Handle both dict and object state
    if isinstance(state, dict):
        current_iter = state.get("current_iteration", 0)
        mission_outputs = state.get("mission_planner_outputs", {})
        aero_outputs = state.get("aerodynamics_outputs", {})
        prop_outputs = state.get("propulsion_outputs", {})
        struct_outputs = state.get("structures_outputs", {})
        mfg_outputs = state.get("manufacturing_outputs", {})
    else:
        current_iter = state.current_iteration
        mission_outputs = state.mission_planner_outputs
        aero_outputs = state.aerodynamics_outputs
        prop_outputs = state.propulsion_outputs
        struct_outputs = state.structures_outputs
        mfg_outputs = state.manufacturing_outputs
    
    for iteration in range(current_iter + 1):
        agents_active = []
        if iteration in mission_outputs:
            agents_active.append("Mission")
        if iteration in aero_outputs:
            agents_active.append("Aero")
        if iteration in prop_outputs:
            agents_active.append("Prop")
        if iteration in struct_outputs:
            agents_active.append("Struct")
        if iteration in mfg_outputs:
            agents_active.append("Mfg")
        
        if agents_active:
            print(f"Iteration {iteration}: {', '.join(agents_active)}")


def get_project_statistics(state) -> dict:
    """Get project completion statistics."""
    # Handle both dict and object state
    if isinstance(state, dict):
        mailboxes = state.get("mailboxes", {})
        mission_outputs = state.get("mission_planner_outputs", {})
        aero_outputs = state.get("aerodynamics_outputs", {})
        prop_outputs = state.get("propulsion_outputs", {})
        struct_outputs = state.get("structures_outputs", {})
        mfg_outputs = state.get("manufacturing_outputs", {})
        current_iter = state.get("current_iteration", 0)
        project_complete = state.get("project_complete", False)
    else:
        mailboxes = state.mailboxes
        mission_outputs = state.mission_planner_outputs
        aero_outputs = state.aerodynamics_outputs
        prop_outputs = state.propulsion_outputs
        struct_outputs = state.structures_outputs
        mfg_outputs = state.manufacturing_outputs
        current_iter = state.current_iteration
        project_complete = state.project_complete
    
    total_messages = sum(len(mailbox.messages) for mailbox in mailboxes.values())
    
    agents_completed = sum(1 for outputs in [
        mission_outputs,
        aero_outputs,
        prop_outputs,
        struct_outputs,
        mfg_outputs
    ] if outputs)
    
    return {
        "total_iterations": current_iter,
        "total_messages": total_messages,
        "agents_completed": agents_completed,
        "project_complete": project_complete
    }