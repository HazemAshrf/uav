#!/usr/bin/env python3
"""Main entry point for the Static Agent Dashboard system."""

import subprocess
import sys
import os
from pathlib import Path

<<<<<<< HEAD
=======
# Add backend to path for cross-platform utilities
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from cross_platform_utils import (
    CrossPlatformEmoji, CrossPlatformNetwork, 
    CrossPlatformPaths, get_platform_info
)

>>>>>>> ae778f3 (second commit)

def check_uv():
    """Check if uv is available."""
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def sync_dependencies():
    """Sync dependencies with uv."""
<<<<<<< HEAD
    print("📦 Syncing dependencies with uv...")
    try:
        subprocess.run(["uv", "sync"], check=True)
        print("✅ Dependencies synced successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to sync dependencies: {e}")
=======
    print(f"{CrossPlatformEmoji.get('📦')} Syncing dependencies with uv...")
    try:
        subprocess.run(["uv", "sync"], check=True)
        print(f"{CrossPlatformEmoji.get('✅')} Dependencies synced successfully")
    except subprocess.CalledProcessError as e:
        print(f"{CrossPlatformEmoji.get('❌')} Failed to sync dependencies: {e}")
>>>>>>> ae778f3 (second commit)
        sys.exit(1)


def run_streamlit_app():
    """Run the Streamlit frontend application."""
<<<<<<< HEAD
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
=======
    print(f"{CrossPlatformEmoji.get('🚀')} Starting Static Agent Dashboard...")
    
    # Use cross-platform paths
    frontend_path = CrossPlatformPaths.get_frontend_path()
    main_app = frontend_path / "main.py"
    
    # Get platform-optimized network config
    network_config = CrossPlatformNetwork.get_host_config()
    browser_url = CrossPlatformNetwork.get_browser_url()
    
    print(f"{CrossPlatformEmoji.get('📱')} Open your browser to: {browser_url}")
    
    try:
        # Build streamlit command with cross-platform config
        cmd = [
            "uv", "run", "streamlit", "run", str(main_app),
            "--server.port", str(network_config["port"]),
            "--server.address", network_config["host"]
        ]
        
        # Run streamlit with proper working directory
        subprocess.run(cmd, cwd=str(frontend_path), check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"{CrossPlatformEmoji.get('❌')} Failed to run application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{CrossPlatformEmoji.get('🛑')} Application stopped by user")


def show_platform_info():
    """Show platform information for debugging."""
    if "--debug" in sys.argv:
        print("\n--- Platform Information ---")
        info = get_platform_info()
        for key, value in info.items():
            print(f"{key}: {value}")
        print("---------------------------\n")
>>>>>>> ae778f3 (second commit)


def main():
    """Main entry point."""
<<<<<<< HEAD
    print("🤖 Static Agent Dashboard System")
=======
    # Show platform info if requested
    show_platform_info()
    
    print(f"{CrossPlatformEmoji.get('🤖')} Static Agent Dashboard System")
>>>>>>> ae778f3 (second commit)
    print("=" * 40)
    
    # Parse command line arguments for help
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
<<<<<<< HEAD
        print("Usage: python main.py")
=======
        print("Usage: python main.py [--debug]")
>>>>>>> ae778f3 (second commit)
        print("")
        print("Starts the Static Agent Dashboard UI.")
        print("Workflow execution is available via the Workflow Status page.")
        print("")
<<<<<<< HEAD
=======
        print("Options:")
        print("  --debug     Show platform information")
        print("")
        print("Environment Variables:")
        print("  OPENAI_API_KEY      Required for LLM functionality")
        print("  STREAMLIT_HOST      Override default host (default: 127.0.0.1)")
        print("  STREAMLIT_PORT      Override default port (default: 8501)")
        print("  ENABLE_EMOJIS       Enable emojis on Windows (default: false)")
        print("  PYTHONUTF8          Enable UTF-8 mode (default: 1)")
        print("")
>>>>>>> ae778f3 (second commit)
        print("Alternative usage:")
        print("  uv run python main.py")
        sys.exit(0)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
<<<<<<< HEAD
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-api-key'")
=======
        print(f"{CrossPlatformEmoji.get('⚠️')} Warning: OPENAI_API_KEY environment variable not set")
        print("   Set it with:")
        print("   - Windows: set OPENAI_API_KEY=your-api-key")
        print("   - Unix/WSL: export OPENAI_API_KEY='your-api-key'")
>>>>>>> ae778f3 (second commit)
        print("   The system may not function properly without it.")
        print()
    
    # Check if uv is available and sync dependencies
    if check_uv():
        sync_dependencies()
    else:
<<<<<<< HEAD
        print("⚠️  uv not found - dependencies may not be up to date")
=======
        print(f"{CrossPlatformEmoji.get('⚠️')} uv not found - dependencies may not be up to date")
>>>>>>> ae778f3 (second commit)
        print("   Install with: pip install uv")
        print()
    
    # Run the application
    run_streamlit_app()


if __name__ == "__main__":
    main()