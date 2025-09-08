# ai_code_reviewer/analysis/report_generator.py

import json
import os
from datetime import datetime


import json
import os

def detect_language(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
    }
    return mapping.get(ext, "unknown")


import json
from analysis.language_detector import detect_language

class ReportGenerator:
    def __init__(self, file_path):
        self.file_path = file_path
        self.language = detect_language(file_path)

    def format_output(self, raw_output):
        formatted = []

        if not raw_output:
            return "[Info] No issues found ✅"

        if self.language == "python":
            try:
                issues = json.loads(raw_output)
                for issue in issues:
                    line = issue.get("line")
                    col = issue.get("column")
                    msg = issue.get("message")
                    typ = issue.get("type").capitalize()
                    formatted.append(f"[{typ}] line {line}:{col} -> {msg}")
            except:
                formatted.append(raw_output)

        elif self.language == "javascript":
            try:
                issues = json.loads(raw_output)
                for file_issues in issues:
                    file_name = file_issues.get("filePath", "unknown")
                    for m in file_issues.get("messages", []):
                        line = m.get("line")
                        col = m.get("column")
                        msg = m.get("message")
                        rule = m.get("ruleId")
                        severity = "Error" if m.get("severity") == 2 else "Warning"
                        formatted.append(f"[{severity}] {file_name}:{line}:{col} -> {msg} ({rule})")
            except:
                formatted.append(raw_output)

        else:  # Java, C, C++ → raw compiler/cppcheck output
            for line in raw_output.splitlines():
                if line.strip():
                    formatted.append(line)

        return "\n".join(formatted)





def generate_report(result, output_path="analysis_report.txt", json_path="analysis_report.json"):
    """Generate both text and JSON reports from the analysis result."""

    # ---- TXT REPORT ----
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("AI Code Reviewer - Analysis Report\n")
        f.write("=" * 60 + "\n")
        f.write(f"📄 File: {result['file']}\n")
        f.write(f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 60 + "\n")

        if result.get("score") is not None:
            f.write(f"📊 Score: {result['score']:.2f}/10\n")
        else:
            f.write("📊 Score: N/A/10\n")

        if result.get("issues"):
            f.write("\n⚠️ Issues:\n")
            for issue in result["issues"]:
                f.write(
                    f" - {issue.get('path', result['file'])}:"
                    f"{issue.get('line', 0)}:"
                    f"{issue.get('column', 0)}: "
                    f"{issue.get('message-id', '')}: {issue.get('message', '')}\n"
                )
        else:
            f.write("\n✅ No issues found!\n")

        if result.get("suggestions"):
            f.write("\n💡 Suggestions:\n")
            for s in result["suggestions"]:
                f.write(f" - {s}\n")

    # ---- JSON REPORT ----
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(result, jf, indent=4, ensure_ascii=False)

    print(f"\n📂 Reports generated: {os.path.abspath(output_path)}, {os.path.abspath(json_path)}")
