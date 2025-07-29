"""Cross-platform compatibility utilities for WSL/Windows deployment."""

import os
import sys
import platform
import tempfile
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union
import threading

# Detect platform and environment
IS_WINDOWS = platform.system() == "Windows"
IS_WSL = "microsoft" in platform.uname().release.lower() if not IS_WINDOWS else False
IS_UNIX = platform.system() in ["Linux", "Darwin"] and not IS_WSL


class CrossPlatformEmoji:
    """Handle emoji display across different platforms and terminals."""
    
    # Emoji mappings with fallbacks
    EMOJI_MAP = {
        "🤖": {"utf8": "🤖", "fallback": "[BOT]"},
        "💬": {"utf8": "💬", "fallback": "[CHAT]"},
        "📊": {"utf8": "📊", "fallback": "[STATUS]"},
        "🚀": {"utf8": "🚀", "fallback": "[ROCKET]"},
        "✅": {"utf8": "✅", "fallback": "[OK]"},
        "❌": {"utf8": "❌", "fallback": "[ERROR]"},
        "⚠️": {"utf8": "⚠️", "fallback": "[WARN]"},
        "🔍": {"utf8": "🔍", "fallback": "[SEARCH]"},
        "🔧": {"utf8": "🔧", "fallback": "[TOOL]"},
        "🎉": {"utf8": "🎉", "fallback": "[SUCCESS]"},
        "🏁": {"utf8": "🏁", "fallback": "[FINISH]"},
        "🔒": {"utf8": "🔒", "fallback": "[LOCK]"},
        "🔄": {"utf8": "🔄", "fallback": "[REFRESH]"},
        "↔️": {"utf8": "↔️", "fallback": "<->"},
    }
    
    @classmethod
    def _supports_utf8(cls) -> bool:
        """Check if the current environment supports UTF-8 emojis."""
        # Check environment variables
        if os.environ.get("PYTHONUTF8") == "1":
            return True
        
        # Check encoding
        try:
            encoding = sys.stdout.encoding or ""
            if "utf-8" in encoding.lower() or "utf8" in encoding.lower():
                return True
        except:
            pass
        
        # Conservative approach: disable emojis on Windows unless explicitly enabled
        if IS_WINDOWS:
            return os.environ.get("ENABLE_EMOJIS", "").lower() in ["1", "true", "yes"]
        
        # Enable on Unix/Linux by default
        return True
    
    @classmethod
    def get(cls, emoji: str) -> str:
        """Get emoji or fallback based on platform support."""
        if emoji not in cls.EMOJI_MAP:
            return emoji
        
        if cls._supports_utf8():
            return cls.EMOJI_MAP[emoji]["utf8"]
        else:
            return cls.EMOJI_MAP[emoji]["fallback"]
    
    @classmethod
    def safe_format(cls, text: str) -> str:
        """Replace all emojis in text with platform-appropriate versions."""
        result = text
        for emoji, mapping in cls.EMOJI_MAP.items():
            if cls._supports_utf8():
                # Keep original emoji
                continue
            else:
                # Replace with fallback
                result = result.replace(emoji, mapping["fallback"])
        return result


class CrossPlatformFileOperations:
    """Handle file operations that work across platforms."""
    
    @staticmethod
    def safe_file_lock_write(file_path: Union[str, Path], data: Dict[str, Any], timeout: float = 5.0) -> bool:
        """Write to file with cross-platform locking mechanism."""
        file_path = Path(file_path)
        lock_file = file_path.with_suffix(file_path.suffix + ".lock")
        
        try:
            # Simple file-based locking (works on all platforms)
            start_time = time.time()
            while lock_file.exists():
                if time.time() - start_time > timeout:
                    return False
                time.sleep(0.1)
            
            # Create lock file
            lock_file.touch()
            
            # Write data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False
        finally:
            # Remove lock file
            try:
                if lock_file.exists():
                    lock_file.unlink()
            except:
                pass
    
    @staticmethod
    def safe_file_lock_read(file_path: Union[str, Path], timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Read from file with cross-platform locking mechanism."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return None
        
        lock_file = file_path.with_suffix(file_path.suffix + ".lock")
        
        try:
            # Wait for lock to be released
            start_time = time.time()
            while lock_file.exists():
                if time.time() - start_time > timeout:
                    break
                time.sleep(0.1)
            
            # Read data
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None


class CrossPlatformPaths:
    """Handle path operations across platforms."""
    
    @staticmethod
    def get_project_root() -> Path:
        """Get the project root directory reliably."""
        # Start from current file and walk up to find project markers
        current = Path(__file__).parent
        
        # Look for common project markers
        markers = ["pyproject.toml", "requirements.txt", "main.py", ".git"]
        
        for _ in range(10):  # Prevent infinite loop
            for marker in markers:
                if (current / marker).exists():
                    return current
            
            parent = current.parent
            if parent == current:  # Reached root
                break
            current = parent
        
        # Fallback to current directory's parent
        return Path(__file__).parent.parent
    
    @staticmethod
    def get_backend_path() -> Path:
        """Get backend directory path."""
        return CrossPlatformPaths.get_project_root() / "backend"
    
    @staticmethod
    def get_frontend_path() -> Path:
        """Get frontend directory path."""
        return CrossPlatformPaths.get_project_root() / "frontend"
    
    @staticmethod
    def get_temp_file_path(filename: str) -> Path:
        """Get temporary file path that works across platforms."""
        temp_dir = Path(tempfile.gettempdir())
        return temp_dir / filename
    
    @staticmethod
    def add_path_to_sys(path: Union[str, Path]) -> None:
        """Safely add path to sys.path if not already present."""
        path_str = str(Path(path).resolve())
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


class CrossPlatformNetwork:
    """Handle network configuration across platforms."""
    
    DEFAULT_HOST = "127.0.0.1"  # More reliable than localhost
    DEFAULT_PORT = 8501
    
    @classmethod
    def get_host_config(cls) -> Dict[str, Union[str, int]]:
        """Get host configuration optimized for the current platform."""
        config = {
            "host": os.environ.get("STREAMLIT_HOST", cls.DEFAULT_HOST),
            "port": int(os.environ.get("STREAMLIT_PORT", cls.DEFAULT_PORT)),
        }
        
        # Platform-specific optimizations
        if IS_WSL:
            # WSL may need 0.0.0.0 to be accessible from Windows
            if config["host"] == "localhost":
                config["host"] = "0.0.0.0"
        
        return config
    
    @classmethod
    def get_browser_url(cls) -> str:
        """Get the URL for browser access."""
        config = cls.get_host_config()
        host = config["host"]
        port = config["port"]
        
        # For display purposes, convert 0.0.0.0 back to localhost
        if host == "0.0.0.0":
            host = "localhost"
        
        return f"http://{host}:{port}"


def setup_utf8_environment():
    """Set up UTF-8 environment for better cross-platform compatibility."""
    # Set UTF-8 environment variables
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    
    # Try to set console encoding on Windows
    if IS_WINDOWS:
        try:
            import locale
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except:
                pass  # Fallback to system default


def get_platform_info() -> Dict[str, Any]:
    """Get platform information for debugging."""
    return {
        "platform": platform.system(),
        "is_windows": IS_WINDOWS,
        "is_wsl": IS_WSL,
        "is_unix": IS_UNIX,
        "python_version": sys.version,
        "encoding": sys.stdout.encoding,
        "utf8_support": CrossPlatformEmoji._supports_utf8(),
        "temp_dir": str(Path(tempfile.gettempdir())),
        "cwd": str(Path.cwd()),
    }


# Initialize UTF-8 environment on import
setup_utf8_environment()