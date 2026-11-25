import os
# Run this script to see the structure of the project directory in a tree format.
IGNORE = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    ".pytest_cache",
    ".idea",
    ".vscode"
}

def show_tree(path, prefix=""):
    entries = sorted(
        [
            entry for entry in os.listdir(path)
            if entry not in IGNORE
        ]
    )

    for index, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        is_last = index == len(entries) - 1

        print(prefix + ("└── " if is_last else "├── ") + entry)

        if os.path.isdir(full_path):
            extension = "    " if is_last else "│   "
            show_tree(full_path, prefix + extension)

show_tree(".")
#To see the structure of the project directory in a tree format, run this script using the command:
# python show_structure.py