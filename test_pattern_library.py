import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.admin_learning.learning_routes import get_pattern_library

print("Testing get_pattern_library() function...")
patterns = get_pattern_library()
print(f"Function returned {len(patterns)} patterns")

if patterns:
    print("\nFirst pattern:")
    for key, value in patterns[0].items():
        print(f"- {key}: {value}")
else:
    print("No patterns returned")
