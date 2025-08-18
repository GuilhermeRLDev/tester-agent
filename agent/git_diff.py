import subprocess

def get_changed_files(base="origin/main"):
    """Return dict {filename: diff}"""
    cmd = ["git", "diff", base, "--unified=0", "--", "*.cs"]
    diff_output = subprocess.check_output(cmd).decode("utf-8")

    diffs = {}
    current_file = None
    current_diff = []

    for line in diff_output.splitlines():
        if line.startswith("+++ b/"):
            if current_file and current_diff:
                diffs[current_file] = "\n".join(current_diff)
                current_diff = []
            current_file = line[6:]
        elif current_file:
            current_diff.append(line)

    if current_file and current_diff:
        diffs[current_file] = "\n".join(current_diff)

    return diffs
