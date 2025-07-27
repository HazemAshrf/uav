#!/usr/bin/env python3
"""Main entry point for the Static Agent Dashboard system."""

import subprocess
import sys
import os
from pathlib import Path


def check_uv():
    """Check if uv is available."""
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def sync_dependencies():
    """Sync dependencies with uv."""
    print("📦 Syncing dependencies with uv...")
    try:
        subprocess.run(["uv", "sync"], check=True)
        print("✅ Dependencies synced successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to sync dependencies: {e}")
        sys.exit(1)


def run_streamlit_app():
    """Run the Streamlit frontend application."""
    print("🚀 Starting Static Agent Dashboard...")
    
    frontend_path = Path(__file__).parent / "frontend"
    main_app = frontend_path / "main.py"
    
    print(f"📱 Open your browser to: http://localhost:8501")
    
    try:
        # Change to frontend directory and run streamlit
        subprocess.run([
            "uv", "run", "streamlit", "run", str(main_app),
            "--server.port", "8501",
            "--server.address", "localhost"
        ], cwd=str(frontend_path), check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")


def main():
    """Main entry point."""
    print("🤖 Static Agent Dashboard System")
    print("=" * 40)
    
    # Parse command line arguments for help
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("Usage: python main.py")
        print("")
        print("Starts the Static Agent Dashboard UI.")
        print("Workflow execution is available via the Workflow Status page.")
        print("")
        print("Alternative usage:")
        print("  uv run python main.py")
        sys.exit(0)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-api-key'")
        print("   The system may not function properly without it.")
        print()
    
    # Check if uv is available and sync dependencies
    if check_uv():
        sync_dependencies()
    else:
        print("⚠️  uv not found - dependencies may not be up to date")
        print("   Install with: pip install uv")
        print()
    
    # Run the application
    run_streamlit_app()


if __name__ == "__main__":
    main()