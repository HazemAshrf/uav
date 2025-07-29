#!/usr/bin/env python3
"""Cross-platform startup script with automatic environment setup."""

import os
import sys
import platform
import subprocess
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from cross_platform_utils import (
    setup_utf8_environment, get_platform_info, 
    CrossPlatformEmoji, CrossPlatformNetwork
)

def print_platform_diagnostics():
    """Print diagnostic information for troubleshooting."""
    print(f"{CrossPlatformEmoji.get('🔍')} Platform Diagnostics")
    print("=" * 50)
    
    info = get_platform_info()
    for key, value in info.items():
        print(f"{key:15}: {value}")
    
    print(f"\nNetwork Configuration:")
    net_config = CrossPlatformNetwork.get_host_config()
    for key, value in net_config.items():
        print(f"{key:15}: {value}")
    
    print("=" * 50)

def setup_windows_environment():
    """Set up Windows-specific environment optimizations."""
    if platform.system() != "Windows":
        return
    
    print(f"{CrossPlatformEmoji.get('🔧')} Setting up Windows environment...")
    
    # Set console encoding to UTF-8
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        print(f"{CrossPlatformEmoji.get('✅')} UTF-8 locale configured")
    except:
        print(f"{CrossPlatformEmoji.get('⚠️')} Could not set UTF-8 locale")
    
    # Set environment variables for better performance
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    
    # Suggest Windows Terminal for better emoji support
    if not os.environ.get("WT_SESSION"):
        print(f"{CrossPlatformEmoji.get('💡')} Tip: Use Windows Terminal for best emoji support")
        print("   Download from Microsoft Store or GitHub")

def check_dependencies():
    """Check that required dependencies are available."""
    print(f"{CrossPlatformEmoji.get('📦')} Checking dependencies...")
    
    required_packages = [
        "streamlit", "langgraph", "langchain", "openai", "pydantic"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"{CrossPlatformEmoji.get('✅')} {package}")
        except ImportError:
            missing.append(package)
            print(f"{CrossPlatformEmoji.get('❌')} {package} (missing)")
    
    if missing:
        print(f"\n{CrossPlatformEmoji.get('⚠️')} Missing packages detected:")
        print("Install with: pip install " + " ".join(missing))
        print("Or use: uv sync")
        return False
    
    return True

def optimize_for_performance():
    """Apply performance optimizations."""
    print(f"{CrossPlatformEmoji.get('🚀')} Applying performance optimizations...")
    
    # Set Python optimization flags
    os.environ.setdefault("PYTHONOPTIMIZE", "1")
    
    # Disable debug features in production
    os.environ.setdefault("STREAMLIT_LOGGER_LEVEL", "WARNING")
    
    # Set efficient JSON handling
    os.environ.setdefault("ORJSON_ENABLED", "1")
    
    print(f"{CrossPlatformEmoji.get('✅')} Performance optimizations applied")

def show_startup_tips():
    """Show platform-specific startup tips."""
    system = platform.system()
    
    print(f"\n{CrossPlatformEmoji.get('💡')} Platform-Specific Tips:")
    
    if system == "Windows":
        print("• Use Windows Terminal for best display quality")
        print("• Set ENABLE_EMOJIS=1 to force enable emojis")
        print("• Consider using WSL for Linux-like experience")
    elif "microsoft" in platform.uname().release.lower():
        print("• WSL detected - using optimized network settings")
        print("• Access from Windows: use localhost or 127.0.0.1")
        print("• File performance: keep files in WSL filesystem")
    else:
        print("• Unix/Linux environment detected")
        print("• Full emoji support available")
        print("• Optimal performance expected")

def main():
    """Main startup function."""
    print(f"{CrossPlatformEmoji.get('🚀')} Cross-Platform UAV Design System")
    print("=" * 60)
    
    # Show diagnostics if requested
    if "--debug" in sys.argv or "--diagnostics" in sys.argv:
        print_platform_diagnostics()
        print()
    
    # Setup environment
    setup_utf8_environment()
    setup_windows_environment()
    
    # Check dependencies
    if not check_dependencies():
        print(f"\n{CrossPlatformEmoji.get('❌')} Dependency check failed")
        print("Please install missing packages and try again")
        sys.exit(1)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print(f"\n{CrossPlatformEmoji.get('⚠️')} OPENAI_API_KEY not set")
        print("Set your API key:")
        if platform.system() == "Windows":
            print("  set OPENAI_API_KEY=your-key-here")
        else:
            print("  export OPENAI_API_KEY='your-key-here'")
        print()
    
    # Apply optimizations
    optimize_for_performance()
    
    # Show tips
    show_startup_tips()
    
    print(f"\n{CrossPlatformEmoji.get('✅')} Environment setup complete!")
    print(f"{CrossPlatformEmoji.get('🚀')} Starting application...")
    
    # Import and run main application
    try:
        import main
        main.main()
    except KeyboardInterrupt:
        print(f"\n{CrossPlatformEmoji.get('🛑')} Shutdown requested by user")
    except Exception as e:
        print(f"\n{CrossPlatformEmoji.get('❌')} Startup failed: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()