#!/usr/bin/env python3
"""Fix cross-platform path issues in all agent files."""

from pathlib import Path
import re

def fix_agent_file(file_path: Path):
    """Fix path handling in a single agent file."""
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match the old path handling
        old_pattern = r'''import sys
import os

# Add parent directory to path to import backend modules
current_dir = os\.path\.dirname\(__file__\)
backend_dir = os\.path\.dirname\(current_dir\)
sys\.path\.append\(backend_dir\)'''
        
        # Replacement with cross-platform handling
        new_pattern = '''import sys
import os
from pathlib import Path

# Add parent directory to path to import backend modules using pathlib
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
sys.path.insert(0, str(backend_dir))'''
        
        # Apply the fix
        updated_content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)
        
        # Check if any changes were made
        if updated_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"⚠️ No changes needed: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all agent files."""
    backend_path = Path(__file__).parent / "backend"
    agents_path = backend_path / "agents"
    
    if not agents_path.exists():
        print(f"Agents directory not found: {agents_path}")
        return
    
    # List of agent files to fix
    agent_files = [
        "mission_planner.py",
        "aerodynamics.py", 
        "propulsion.py",
        "structures.py",
        "manufacturing.py",
        "coordinator.py"
    ]
    
    fixed_count = 0
    for agent_file in agent_files:
        file_path = agents_path / agent_file
        if fix_agent_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} agent files for cross-platform compatibility")

if __name__ == "__main__":
    main()