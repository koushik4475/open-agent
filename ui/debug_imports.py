
import sys
import os
from pathlib import Path

# Add parent directory of the project to path to support 'import openagent'
# ui/debug_imports.py -> ui -> openagent -> parent
project_root = Path(__file__).resolve().parent.parent
print(f"Project root: {project_root}")
sys.path.insert(0, str(project_root.parent))
print(f"Sys path[0]: {sys.path[0]}")
os.chdir(project_root)

try:
    print("Attempting to import openagent...")
    import openagent
    print(f"Success! openagent file: {openagent.__file__}")
    
    print("Attempting to import openagent.core.agent...")
    from openagent.core.agent import Agent
    print("Success! Agent imported.")
    
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
