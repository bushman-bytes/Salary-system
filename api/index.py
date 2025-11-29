"""
Vercel serverless function entry point for FastAPI application.
"""
import sys
import os
from pathlib import Path
import importlib.util

# Add project root to Python path FIRST
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set working directory to project root for static files and templates
os.chdir(project_root)

# CRITICAL: Import the app package FIRST to register it in sys.modules
# This ensures that when app.py tries to import "from app.config.config",
# Python will find the app/ package, not app.py
try:
    # Import the app package to register it in sys.modules
    import app
    # Verify it's the package, not the file
    if not hasattr(app, '__path__'):
        # If app is a file module, we need to remove it and import the package
        if 'app' in sys.modules:
            del sys.modules['app']
        # Now import the package
        import app
except ImportError as e:
    print(f"Warning: Could not import app package: {e}")

# Now ensure app.py is NOT in sys.modules as 'app'
# Remove it if it exists
if 'app' in sys.modules:
    mod = sys.modules['app']
    # Check if it's a file module (app.py) not a package
    if not hasattr(mod, '__path__'):
        # It's app.py, remove it
        del sys.modules['app']
        # Re-import the package
        import app

# Now load main.py (renamed from app.py to avoid conflict) as a separate module
try:
    # Load main.py (app.py has been renamed to avoid conflict)
    app_file_path = project_root / "main.py"
    
    if not app_file_path.exists():
        raise FileNotFoundError(f"main.py not found at {project_root}. Please ensure app.py has been renamed to main.py.")
    
    # Load the file as "main_app" module to avoid any conflicts
    spec = importlib.util.spec_from_file_location("main_app", app_file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create spec for {app_file_path}")
    
    main_app_module = importlib.util.module_from_spec(spec)
    
    # Register it with a unique name
    sys.modules["main_app"] = main_app_module
    
    # Execute the module - now when it does "from app.config.config",
    # Python will find the app/ package (already in sys.modules)
    spec.loader.exec_module(main_app_module)
    
    # Get the FastAPI app instance
    app = main_app_module.app
    
except Exception as e:
    # Better error handling for debugging
    import traceback
    print(f"Error importing app: {e}")
    print(f"Project root: {project_root}")
    print(f"App file path: {app_file_path}")
    print(f"App file exists: {app_file_path.exists() if 'app_file_path' in locals() else 'N/A'}")
    print(f"App package in sys.modules: {'app' in sys.modules}")
    if 'app' in sys.modules:
        print(f"App module type: {type(sys.modules['app'])}")
        print(f"App module has __path__: {hasattr(sys.modules['app'], '__path__')}")
    print(f"Python path: {sys.path}")
    traceback.print_exc()
    raise

# Export the app for Vercel
handler = app
