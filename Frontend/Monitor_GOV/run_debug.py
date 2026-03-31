import sys
import os
from pathlib import Path
import json

# Add current directory to path
sys.path.append(os.getcwd())

from main import collect

def run():
    print("Starting collection...")
    # Run with fewer pages/days for quick test
    try:
        result = collect(max_pages=1, out_path=Path("debug_result.json"))
        print(f"Collection complete. Found {result.get('count')} items.")
        print(f"Results saved to debug_result.json")
        
        # Show top 3 items
        if result.get('items'):
            print("\nTop 3 items:")
            for item in result['items'][:3]:
                print(f"- [{item.get('source')}] {item.get('title')} ({item.get('date')})")
    except Exception as e:
        print(f"Error during collection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run()
