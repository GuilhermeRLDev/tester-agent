from agent.code_embedings import get_dependency_tree_for_method

def retrieve_code_context(unit, graph):
    """
    Retrieve code context for the changed method.
    Returns a string with class and method names.
    """
    namespace = unit.get("namespace", "")
    class_name = unit.get("class", "")
    method_name = unit.get("method", "")

    if not namespace or not class_name or not method_name:
        return "No valid class or method found."

    # Get the code for the method
    method_code = get_dependency_tree_for_method(f"{namespace}.{class_name}.{method_name}", graph)

    if not method_code:
        return f"Method {method_name} not found in the graph."

    return method_code

#ChromaDB for unit tests examples and standards
def retrieve_context(unit):
    """
    Retrieve existing tests for the unit.
    Returns a string with existing test code or a message if none found.
    """
    # This is a placeholder for actual implementation
    # In a real scenario, this would query a database or file system for existing tests
    return "No existing tests found."

def build_prompt(unit, graph, existing_tests="None encountered"):
    return f"""
You are an AI generating XUnit tests in C#.
Use Arrange-Act-Assert pattern, and Moq for dependencies.
Target class: {unit['class']}
Changed method: {unit['signature']}

Existing unit test class:
{existing_tests}

Git diff snippet:
{unit['diff']}

Classes and methods invoked by the changed method:
{retrieve_code_context(unit, graph)}

Similar unit tests:
{retrieve_context(unit)}

1- Output only the C# test class code.
2- Refactor class existing clas to include method or write a new class if it does not exist.
4- Refactor existing tests in case change requires it
5- Pay attention to the class and methods block should be valid C# code.
"""
