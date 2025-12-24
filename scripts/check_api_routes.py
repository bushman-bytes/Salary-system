"""
Check if salary payment API routes are registered.
Run this to verify routes are accessible.
"""
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from main import app
    
    print("=" * 60)
    print("Checking API Routes")
    print("=" * 60)
    
    # Get all routes
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                'path': route.path,
                'methods': list(route.methods) if route.methods else []
            })
    
    # Find salary payment routes
    salary_routes = [r for r in routes if 'salary' in r['path'].lower()]
    
    print(f"\nTotal routes: {len(routes)}")
    print(f"Salary-related routes: {len(salary_routes)}\n")
    
    if salary_routes:
        print("Salary payment routes found:")
        for route in salary_routes:
            methods = ', '.join([m for m in route['methods'] if m != 'HEAD' and m != 'OPTIONS'])
            print(f"  ✓ {methods:6} {route['path']}")
    else:
        print("✗ No salary payment routes found!")
        print("\nThis means the routes aren't being registered.")
        print("Possible causes:")
        print("  1. Import error preventing route registration")
        print("  2. Routes defined after an error")
        print("  3. Server needs restart")
    
    # Check for POST route specifically
    post_route = [r for r in salary_routes if 'POST' in r['methods'] and 'salary-payments' in r['path']]
    if post_route:
        print(f"\n✓ POST /api/salary-payments route is registered!")
    else:
        print(f"\n✗ POST /api/salary-payments route NOT found!")
        print("   The route may not be registered. Check for import errors.")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    import traceback
    print(f"Error loading app: {str(e)}")
    print(f"\nTraceback:\n{traceback.format_exc()}")
    sys.exit(1)
