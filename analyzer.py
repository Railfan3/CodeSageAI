import ast
import os
import subprocess
import json
import html
import radon.complexity as radon_complexity
from radon.metrics import mi_visit


import subprocess
import json
import os

import subprocess
import json
import os
from analysis.language_detector import detect_language

class CodeAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.language = detect_language(file_path)

    def analyze(self):
        if self.language == "python":
            return self._run_command(["pylint", "--output-format=json", self.file_path])
        
        elif self.language == "javascript":
            return self._run_command(["eslint", "-f", "json", self.file_path])
        
        elif self.language == "java":
            return self._run_command(["javac", self.file_path])
        
        elif self.language in ["c", "cpp"]:
            return self._run_command(["cppcheck", "--enable=all", "--template=gcc", self.file_path])
        
        else:
            return f"[Error] Unsupported or unknown language for file: {self.file_path}"

    def _run_command(self, command):
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout.strip() or result.stderr.strip()
        except FileNotFoundError:
            return f"[Error] Required tool not installed for {self.language}"







# analysis/analyzer.py
from .language_detector import detect_language
from .error_checker import check_python, check_javascript, check_cpp, check_java
from typing import Dict, Any, List

def analyze_code(code: str, filename: str = None) -> Dict[str, Any]:
    """
    Main analysis entrypoint used by backend.
    Returns a dictionary with keys:
      - score (0-100)
      - maintainability
      - issues (list of dicts)
      - complexity (list)
      - suggestions (list)
      - language
      - file
    """
    lang = detect_language(code, filename)
    lang_str = lang.lower() if lang else "unknown"

    result = {
        "language": lang_str,
        "file": filename or "<submitted>",
        "score": None,
        "maintainability": None,
        "issues": [],
        "complexity": [],
        "suggestions": []
    }

    if "python" in lang_str:
        r = check_python(code, result["file"])
        result.update({
            "issues": r.get("issues", []),
            "complexity": r.get("complexity", []),
            "maintainability": r.get("maintainability"),
            "suggestions": r.get("suggestions", [])
        })
    elif "javascript" in lang_str or "js" in lang_str:
        r = check_javascript(code, result["file"])
        result.update({
            "issues": r.get("issues", []),
            "complexity": r.get("complexity", []),
            "maintainability": r.get("maintainability"),
            "suggestions": r.get("suggestions", [])
        })
    elif "c++" in lang_str or lang_str in ("c", "cpp"):
        r = check_cpp(code, result["file"])
        result.update({
            "issues": r.get("issues", []),
            "suggestions": r.get("suggestions", [])
        })
    elif "java" in lang_str:
        r = check_java(code, result["file"])
        result.update({
            "issues": r.get("issues", []),
            "suggestions": r.get("suggestions", [])
        })
    else:
        # fallback: try Python checks then say unknown
        r = check_python(code, result["file"])
        result.update({
            "issues": r.get("issues", []),
            "complexity": r.get("complexity", []),
            "maintainability": r.get("maintainability"),
            "suggestions": r.get("suggestions", [])
        })
        result["language"] = lang_str

    # Simple scoring: start 100 and penalize issues
    base = 100
    penalty = len(result["issues"]) * 5
    score = max(0, base - penalty)
    result["score"] = float(score)
    return result







def generate_suggestions(result: dict) -> list:
    """Generate AI-like suggestions based on analysis results."""
    suggestions = []

    # Score based
    if result.get("score", 10) < 7:
        suggestions.append("⚠️ Improve code quality to raise Pylint score above 7.")

    # Issues based
    for issue in result.get("issues", []):
        msg_id = issue.get("message-id", "")
        msg = issue.get("message", "")

        if msg_id == "C0114":
            suggestions.append("📝 Add a module-level docstring to describe the purpose of the file.")
        elif msg_id == "C0116":
            suggestions.append("📝 Add docstrings for all functions and methods.")
        elif msg_id == "W0611":
            suggestions.append("🧹 Remove unused imports to keep the code clean.")
        elif msg_id == "W0612":
            suggestions.append("🧹 Remove unused variables to simplify the code.")
        elif msg_id == "R0912":
            suggestions.append("⚡ Too many branches in a function. Consider splitting into smaller functions.")
        elif msg_id == "R0915":
            suggestions.append("⚡ Function has too many statements. Refactor for clarity.")
        else:
            suggestions.append(f"📌 Review: {msg}")

    # Complexity based
    for comp in result.get("complexity", []):
        if comp.complexity > 10:
            suggestions.append(f"⚡ Function `{comp.name}` is very complex (CC={comp.complexity}). Strongly consider refactoring.")
        elif comp.complexity > 5:
            suggestions.append(f"⚡ Function `{comp.name}` is somewhat complex (CC={comp.complexity}). Refactor if possible.")

    # Maintainability index
    if result.get("maintainability", 100) < 65:
        suggestions.append("♻️ Maintainability index is low. Break code into smaller, reusable functions.")

    if not suggestions:
        suggestions.append("✅ Code looks clean! Great job!")

    return list(set(suggestions))  # remove duplicates


def save_html_report(result: dict, suggestions: list, output_file="analysis_report.html"):
    """Save the analysis results to an HTML file."""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("<html><head><title>AI Code Review Report</title>")
        f.write("""
        <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color:#f9f9f9; }
        h2 { color:#2E86C1; }
        .issue { color:#E74C3C; }
        .ok { color:green; }
        .suggestion { color:#8E44AD; }
        .complex { color:#D35400; }
        ul { padding-left:20px; }
        li { margin:4px 0; }
        .report-box { background:white; padding:20px; border-radius:10px; box-shadow:0 0 10px #ccc; }
        </style>
        """)
        f.write("</head><body>")
        f.write("<div class='report-box'>")

        f.write(f"<h2>📄 File: {html.escape(result['file'])}</h2>")
        f.write(f"<p><b>📊 Pylint Score:</b> {result['score']}/10</p>")
        f.write(f"<p><b>📈 Maintainability Index:</b> {result['maintainability']:.2f}</p>")

        f.write("<h3>⚠️ Issues:</h3><ul>")
        if result["issues"]:
            for issue in result["issues"]:
                f.write(f"<li class='issue'>[{issue.get('type','')}] {html.escape(issue.get('message',''))}</li>")
        else:
            f.write("<li class='ok'>✅ No major issues found!</li>")
        f.write("</ul>")

        f.write("<h3>🧩 Complexity Report:</h3><ul>")
        for comp in result["complexity"]:
            css_class = "complex" if comp.complexity > 5 else "ok"
            f.write(f"<li class='{css_class}'>Function <b>{html.escape(comp.name)}</b> → Complexity {comp.complexity}</li>")
        f.write("</ul>")

        f.write("<h3>💡 Suggestions:</h3><ul>")
        for s in suggestions:
            f.write(f"<li class='suggestion'>{html.escape(s)}</li>")
        f.write("</ul>")

        f.write("</div></body></html>")

    print(f"📂 HTML Report saved to {output_file}")
