# test_run.py
from analysis.analyzer import analyze_code

samples = {
    "py_syntax": "def f()\n    print('hi')",
    "py_ok": "def f():\n    print('hello')",
    "js_err": "function x() { console.log('hi' ",
    "cpp_err": "#include <iostream>\nint main() { std::cout << 'hi' }",
    "java_err": "public class Test { public static void main(String[] args) { System.out.println('hi') } }"
}

for name, code in samples.items():
    print("===", name, "===")
    r = analyze_code(code)
    import json
    print(json.dumps(r, indent=2))
    print()
