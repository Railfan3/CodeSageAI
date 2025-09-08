# analysis/error_checker.py
import ast
import tempfile
import subprocess
import os
import re
from typing import List, Dict, Any

# optional JS parser
try:
    import esprima
except Exception:
    esprima = None

# radon for Python complexity & MI
try:
    from radon.complexity import cc_visit, cc_rank
    from radon.metrics import mi_visit
except Exception:
    cc_visit = None
    cc_rank = None
    mi_visit = None


def _write_temp(code: str, suffix: str):
    f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    f.write(code.encode("utf-8"))
    f.flush()
    f.close()
    return f.name


def check_python(code: str, path: str = "<submitted>") -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    complexity: List[Dict[str, Any]] = []
    suggestions: List[str] = []

    # Syntax check using compile/ast
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append({
            "type": "SyntaxError",
            "message": e.msg,
            "path": path,
            "line": getattr(e, "lineno", None),
            "column": getattr(e, "offset", None)
        })
        return {"issues": issues, "complexity": complexity, "suggestions": suggestions}

    # Optional: radon complexity & MI if available
    if cc_visit is not None and mi_visit is not None:
        try:
            comps = cc_visit(code)
            for c in comps:
                complexity.append({
                    "name": c.name,
                    "lineno": c.lineno,
                    "complexity": c.complexity,
                    "rank": cc_rank(c.complexity)
                })
                if c.complexity > 8:
                    suggestions.append(f"Refactor function {c.name} (complexity {c.complexity}).")
            mi = mi_visit(code, True)
        except Exception:
            mi = None
    else:
        mi = None

    # Optional: pylint (if installed) to generate more issues (subprocess)
    try:
        tmp = _write_temp(code, ".py")
        proc = subprocess.run(["pylint", "--output-format=json", tmp],
                              capture_output=True, text=True, timeout=15)
        if proc.stdout:
            import json
            try:
                pyl_issues = json.loads(proc.stdout)
                for p in pyl_issues:
                    issues.append({
                        "type": p.get("type", ""),
                        "message": p.get("message", ""),
                        "path": p.get("path", path),
                        "line": p.get("line"),
                        "column": p.get("column")
                    })
            except Exception:
                pass
    except Exception:
        pass
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass

    return {"issues": issues, "complexity": complexity, "maintainability": mi, "suggestions": suggestions}


def check_javascript(code: str, path: str = "<submitted>") -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    suggestions: List[str] = []

    if esprima is not None:
        try:
            esprima.parseScript(code)
        except Exception as e:
            # esprima error message often contains line/column
            msg = str(e)
            # try extract line/column
            m = re.search(r"Line (\d+):(\d+)", msg)
            if not m:
                m = re.search(r"Line (\d+)", msg)
            line = int(m.group(1)) if m else None
            column = int(m.group(2)) if m and m.lastindex >= 2 else None
            issues.append({
                "type": "SyntaxError",
                "message": msg,
                "path": path,
                "line": line,
                "column": column
            })
    else:
        issues.append({
            "type": "Info",
            "message": "esprima not installed; JS parsing unavailable. pip install esprima",
            "path": path,
            "line": None,
            "column": None
        })

    return {"issues": issues, "complexity": [], "maintainability": None, "suggestions": suggestions}


def check_cpp(code: str, path: str = "<submitted>") -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    suggestions: List[str] = []

    tmp = _write_temp(code, ".cpp")
    try:
        # Use g++ -fsyntax-only
        proc = subprocess.run(["g++", "-fsyntax-only", tmp],
                              capture_output=True, text=True, timeout=10)
        stderr = proc.stderr or proc.stdout
        if stderr:
            # parse lines like: tmp.cpp:3:12: error: ...
            for line in stderr.splitlines():
                m = re.match(r".*:(\d+):(?:(\d+):)?\s*(error|warning):\s*(.*)", line)
                if m:
                    ln = int(m.group(1))
                    col = int(m.group(2)) if m.group(2) else None
                    typ = m.group(3)
                    msg = m.group(4)
                    issues.append({
                        "type": typ,
                        "message": msg.strip(),
                        "path": path,
                        "line": ln,
                        "column": col
                    })
                else:
                    # fallback: add raw line
                    issues.append({
                        "type": "Compiler",
                        "message": line,
                        "path": path,
                        "line": None,
                        "column": None
                    })
    except FileNotFoundError:
        issues.append({
            "type": "ToolMissing",
            "message": "g++ not found on PATH. Install a C++ compiler for C/C++ diagnostics.",
            "path": path,
            "line": None,
            "column": None
        })
    except Exception as e:
        issues.append({"type": "Error", "message": str(e), "path": path, "line": None, "column": None})
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass

    return {"issues": issues, "complexity": [], "maintainability": None, "suggestions": suggestions}


def check_java(code: str, path: str = "<submitted>") -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    suggestions: List[str] = []

    # Write to Main.java (javac requires file name matches class; best-effort)
    tmp = _write_temp(code, ".java")
    try:
        proc = subprocess.run(["javac", tmp], capture_output=True, text=True, timeout=10)
        stderr = proc.stderr or proc.stdout
        if stderr:
            # javac messages: tmp.java:3: error: ';' expected
            for line in stderr.splitlines():
                m = re.match(r".*:(\d+):\s*error:\s*(.*)", line)
                if m:
                    ln = int(m.group(1))
                    msg = m.group(2)
                    issues.append({
                        "type": "error",
                        "message": msg.strip(),
                        "path": path,
                        "line": ln,
                        "column": None
                    })
                else:
                    issues.append({
                        "type": "Compiler",
                        "message": line,
                        "path": path,
                        "line": None,
                        "column": None
                    })
    except FileNotFoundError:
        issues.append({
            "type": "ToolMissing",
            "message": "javac not found on PATH. Install JDK for Java diagnostics.",
            "path": path,
            "line": None,
            "column": None
        })
    except Exception as e:
        issues.append({"type": "Error", "message": str(e), "path": path, "line": None, "column": None})
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass

    return {"issues": issues, "complexity": [], "maintainability": None, "suggestions": suggestions}
