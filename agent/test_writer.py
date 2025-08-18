import os
import re

def write_tests(unit, test_code, test_dir="tests/"):
    os.makedirs(test_dir, exist_ok=True)
    filename = f"{unit['class']}Tests.cs"
    filepath = os.path.join(test_dir, filename)

    code_only_expression = re.compile(r"(?s)```csharp(.*?)```")

    match = code_only_expression.search(test_code)

    if match:
        test_code = match.group(1).strip()
    else:
        print("No C# code block found in the generated test code.")
        return

    # Write required code to the test file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(test_code)

    print(f"✅ Test written: {filepath}")
