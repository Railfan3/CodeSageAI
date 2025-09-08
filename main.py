import os
import argparse
import json
from analysis.analyzer import analyze_code, generate_suggestions, save_html_report


def analyze_path(path: str, output_dir: str):
    """Analyze a single file or all Python files in a directory."""
    results = []

    if os.path.isfile(path) and path.endswith(".py"):
        results.append(analyze_code(path))
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    results.append(analyze_code(full_path))
    else:
        print(f"❌ Invalid path: {path}")
        return

    # Process results
    all_suggestions = []
    for res in results:
        if "error" in res:
            print(f"⚠️ Error analyzing {res.get('file', '?')}: {res['error']}")
            continue

        suggestions = generate_suggestions(res)
        all_suggestions.extend(suggestions)

        # Save per-file HTML
        file_name = os.path.basename(res["file"]).replace(".py", "_report.html")
        file_report_path = os.path.join(output_dir, file_name)
        save_html_report(res, suggestions, output_file=file_report_path)

    # Save combined JSON report
    json_report = os.path.join(output_dir, "analysis_report.json")
    with open(json_report, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print(f"📂 JSON report saved to {json_report}")

    return results, all_suggestions


def main():
    parser = argparse.ArgumentParser(description="AI Code Reviewer CLI")
    parser.add_argument("path", help="Path to Python file or directory")
    parser.add_argument("-o", "--output", default="reports", help="Output directory for reports")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    results, suggestions = analyze_path(args.path, args.output)

    print("\n===== 📊 Analysis Summary =====")
    for res in results:
        if "error" in res:
            continue
        print(f"\n📄 {res['file']}")
        print(f"   🔹 Score: {res['score']}/10")
        print(f"   🔹 Maintainability: {res['maintainability']:.2f}")
        print(f"   🔹 Issues found: {len(res['issues'])}")

    print("\n===== 💡 Suggestions =====")
    if suggestions:
        for s in set(suggestions):
            print(f" - {s}")
    else:
        print("✅ No major suggestions. Code looks clean!")


if __name__ == "__main__":
    main()
