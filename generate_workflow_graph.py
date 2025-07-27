#!/usr/bin/env python3
"""Generate workflow graph visualization."""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

try:
    from langgraph.workflow import create_static_uav_design_workflow
    
    print("🎨 Generating workflow graph visualization...")
    
    # Create the workflow
    workflow = create_static_uav_design_workflow()
    
    # Generate the graph image
    graph_image = workflow.get_graph().draw_mermaid_png()
    
    # Save to root directory
    output_path = Path(__file__).parent / "workflow_graph.png"
    with open(output_path, "wb") as f:
        f.write(graph_image)
    
    print(f"✅ Workflow graph saved to: {output_path}")
    print("📊 Graph shows the corrected flow:")
    print("   coordinator → {continue: aggregator, wait: waiting}")
    print("   aggregator → coordinator")
    print("   waiting → {continue: coordinator, end: END}")
    
except Exception as e:
    print(f"❌ Error generating graph: {e}")
    print("📝 This may require additional dependencies like graphviz.")
    print("Install with: pip install graphviz")
    
    # Fallback: show text representation
    print("\n📋 Workflow Graph Structure (Text):")
    print("""
    START
      ↓
    coordinator_node
    ├─ waiting_for_user_decision = True → waiting_node
    └─ normal flow → aggregator_node
      ↓
    aggregator_node → coordinator_node (cycles back)
    
    waiting_node
    ├─ user_decision = "continue" → coordinator_node (with updated requirements)
    └─ user_decision = "start_new" → END
    
    Key Changes:
    - Coordinator NEVER goes directly to END
    - Only waiting_node can reach END
    - Max iterations check happens IN coordinator_node
    - Frontend/backend communication via progress file
    """)