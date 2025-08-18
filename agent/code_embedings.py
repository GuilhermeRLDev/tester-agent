import os
import json
import re

'''
    Loads all the methos methadata per class
'''
def get_execution_graph(path="../analysis"):
    """
    Get all files in the specified path.
    Returns a list of file paths.
    """
    files = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    
    for file in files:
        roslyn_analysys = json.load(open(file, "r", encoding="utf-8"))

        key_pair_items = {}

        for c in roslyn_analysys:
            for method in c["methods"].keys():
                key = f"{c["class"]}.{method}"
                if  key not in key_pair_items:
                    key_pair_items[key] = c["methods"][method]
                    key_pair_items[key]["file"] = c["file"]
        
    return key_pair_items

def get_methods_per_class_from_file(file_path):
    """
    Get methods per class from a file.
    Returns a dict with method names as keys and method code as values.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    class_name = get_class(content)
    namespace = get_namespace(content)

    # Regex: find method signatures ending with either '{' or '=>'
    signature_pattern = re.compile(
        r"""
        (?P<modifier>\b(public|private|protected|internal|protected\s+internal|private\s+protected)\b\s+)?  
        (?P<static>static\s+)?                                                                               
        (?P<returnType>[a-zA-Z0-9_<>,\[\]\?]+)\s+                                                           
        (?P<methodName>[a-zA-Z_][a-zA-Z0-9_]*)\s*                                                          
        \(
            (?P<parameters>[^)]*)                                                                            
        \)\s*
        (?P<bodyStart>\{|=>)
        """,
        re.VERBOSE
    )

    result = {}

    for match in signature_pattern.finditer(content):
        start = match.start()
        body_start = match.group("bodyStart")
        method_name = match.group("methodName")

        if body_start == "{":
            # Block-bodied: find matching closing brace
            brace_count = 0
            end = start
            for i, ch in enumerate(content[start:], start=start):
                if ch == "{":
                    brace_count += 1
                elif ch == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            method_code = content[start:end].strip()

        else:  # Expression-bodied (=> ... ;)
            semicolon_index = content.find(";", match.end())
            if semicolon_index != -1:
                method_code = content[start:semicolon_index+1].strip()
            else:
                method_code = content[start:].strip()

        result[f"{namespace}.{class_name}.{method_name}"] = method_code

    return result

def get_class(content):
    class_pattern = re.compile(r'class\s+(\w+)')

    class_match = class_pattern.search(content)
    if class_match:
        return class_match.group(1) 
    
    return ""

def get_namespace(content):
    # Match full namespace with dots
    class_pattern = re.compile(r'namespace\s+([\w\.]+)')

    match = class_pattern.search(content)
    if match:
        return match.group(1)
    return ""

def get_dependency_tree_for_method(method, graph):
    methods = get_methods_per_class_from_file("/home/workspace/mistral-quant/OpenBanking4All/PSD2Authentication/PSD2Authentication/PSD2Authentication/Controllers/ConfigurationController.cs")

    if method not in methods:
        print(f"Method {method} not found in the graph.")
        return
    
    root_method = methods[method]

    calls = {}
    implementations = {}
    if method in graph:
        child_call = graph[method]
        
        #load calls that can be parsed
        for c in child_call["calls"]:
            if c not in calls and c in graph:
                calls[c] = {
                        "file": graph[c]["file"],
                        "method": get_methods_per_class_from_file(graph[c]["file"])[implementation]
                    }
                
        for sf in child_call["side_effects"]:
            for implementation in sf["implementations"]:
                if implementation not in implementations and implementation in graph:
                    implementations[implementation] = {
                        "file": graph[implementation]["file"],
                        "method": get_methods_per_class_from_file(graph[implementation]["file"])[implementation]
                    }
                        
    return {
        "root_method": root_method,
        "calls": calls,
        "implementations": implementations
    }
    
