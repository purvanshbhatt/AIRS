import ast
import os
from pathlib import Path
import pytest

# The core determinism invariant (ADR-007) requires these files to NEVER
# import or depend on LLM/generative AI narrative modules.
TARGET_FILES = [
    "app/services/scoring.py",
    "app/services/decision_engine.py",
    "app/services/readiness_drivers.py",
    "app/services/evidence_confidence.py",
    "app/services/ai_frameworks.py",
]

FORBIDDEN_HINTS = {
    "ai_narrative",
    "app.services.intelligence",
    "narrative",
    "llm_narrative",
    "google.genai",
    "google.generativeai"
}

def check_file_for_forbidden_imports(filepath: str):
    path = Path(filepath)
    if not path.exists():
        # If a file hasn't been implemented yet, skip it.
        return
        
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath)
        
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for hint in FORBIDDEN_HINTS:
                    if hint in alias.name:
                        pytest.fail(f"ADR-007 Violation: {filepath} imports forbidden module '{alias.name}' (matched hint '{hint}')")
                        
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for hint in FORBIDDEN_HINTS:
                    if hint in node.module:
                        pytest.fail(f"ADR-007 Violation: {filepath} imports from forbidden module '{node.module}' (matched hint '{hint}')")
            for alias in node.names:
                for hint in FORBIDDEN_HINTS:
                    if hint in alias.name:
                        pytest.fail(f"ADR-007 Violation: {filepath} imports forbidden name '{alias.name}' (matched hint '{hint}')")


@pytest.mark.parametrize("filepath", TARGET_FILES)
def test_file_has_no_llm_imports(filepath):
    """
    Enforce deterministic scoring invariants at the bytecode/AST level.
    Ensures that readiness and scoring components cannot accidentally invoke LLMs.
    """
    check_file_for_forbidden_imports(filepath)
