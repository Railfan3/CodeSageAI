# ai_code_reviewer/tests/test_analyzer.py

import os
import pytest
from analysis.analyzer import analyze_code

def test_analyze_code_sample():
    sample_file = os.path.join("data", "sample_code.py")
    result = analyze_code(sample_file)

    assert isinstance(result, dict)
    assert "file" in result
    assert "issues" in result
    assert isinstance(result["issues"], list)
