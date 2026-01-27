"""Quick test script for building the model."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("Testing model build...")

try:
    from examples.domino_printing_canopy import build_domino_printing_canopy
    print("Import successful")

    model = build_domino_printing_canopy()
    print(f"Model built successfully with {model.element_count} elements")

    # List element types
    from collections import Counter
    types = Counter(e.element_type.value for e in model.get_all_elements())
    print("\nElement counts by type:")
    for elem_type, count in types.items():
        print(f"  {elem_type}: {count}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
