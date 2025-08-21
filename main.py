from agent.git_diff import get_changed_files
from agent.code_parser import extract_units
from agent.prompt_builder import build_prompt
from agent.llm_client import generate_test
from agent.test_writer import write_tests
from agent.code_embedings import get_execution_graph

def main():
    print("🔍 Collecting git diff...")
    diffs = get_changed_files()

    graph = get_execution_graph("/home/workspace/mistral-quant/OpenBanking4All/analysis")
    
    for file, diff in diffs.items():
        print(f"Processing {file}...")
        print(diff)
        units = extract_units(file, diff)
        
        print(f"Found {len(units)} units to test in {file}.")
    
        for unit in units:
            prompt = build_prompt(unit, graph)
            print(prompt)
            test_code = generate_test(prompt)
            write_tests(unit, test_code)

if __name__ == "__main__":
    main()
