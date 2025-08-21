import re

def sanitize_diff(diff_text: str) -> str:
    out = []
    for line in diff_text.splitlines():
        if line.startswith('diff --git') or line.startswith('index ') \
           or line.startswith('--- ') or line.startswith('+++ ') \
           or line.startswith('@@'):
            continue
        if line.startswith('+') or line.startswith(' '):
            out.append(line[1:])  # drop the first diff marker char
    return '\n'.join(out)

def extract_units(file, diff):
    """
    Extract changed methods from C# diff.
    Returns list of dicts: [{ 'class': ..., 'method': ..., 'signature': ..., 'diff': ... }]
    """
    units = []

    method_pattern = re.compile(
    r'(public|private|protected|internal)\s+'      # access modifier
    r'(async\s+)?'                                 # async
    r'([\w<>\[\],\s]+)\s+'                         # return type (allow generics, arrays, spaces)
    r'(\w+)\s*'                                    # method name
    r'\(([^)]*)\)\s*'                              # parameters
    r'(?:=>|{)',                                   # body starts
    re.MULTILINE
    )

    class_pattern = re.compile(r'class\s+(\w+)')
   
    current_class = None
    print(f"Parsing file: {file}")
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()

    class_match = class_pattern.search(content)
    if class_match:
        current_class = class_match.group(1)

    namespace_pattern = re.compile(r'namespace\s+([\w\.]+)')
    current_namespace = ""
    namespace_match = namespace_pattern.search(content)
    if namespace_match:
        current_namespace = namespace_match.group(1)

    for match in method_pattern.finditer(sanitize_diff(diff)):
        units.append({
            "namespace": current_namespace,
            "class": current_class,
            "method": match.group(4),
            "signature": match.group(0),
            "diff": diff
        })

    return units

