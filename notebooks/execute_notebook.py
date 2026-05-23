import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
nb_path = HERE / "02_analysis_and_plots.ipynb"

if not nb_path.exists():
    raise FileNotFoundError(f"Notebook not found at: {nb_path}")

with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Concatenate all code cells
code_lines = []
for cell in nb.get("cells", []):
    if cell.get("cell_type") == "code":
        source = cell.get("source", [])
        # Ensure it's a list of strings
        if isinstance(source, str):
            source = [source]
        for line in source:
            # Skip magic commands like %matplotlib inline or similar if any
            if line.strip().startswith("%"):
                continue
            code_lines.append(line)
        code_lines.append("\n\n")

full_code = "".join(code_lines)

# Set up interactive environment variables and dummy display function
global_env = {
    "__name__": "__main__",
    "display": print,
    "__file__": str(nb_path),
}

print("Executing all code cells from the notebook...")
exec(full_code, global_env)
print("Execution completed successfully!")
