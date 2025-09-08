# AI Code Reviewer

A comprehensive multi-language code analysis tool that provides professional-grade static code analysis, complexity metrics, and actionable feedback for improving code quality.

## Features

- **Multi-Language Support**: Analyze code in Python, JavaScript, TypeScript, Java, C/C++, C#, PHP, Go, Rust, HTML, CSS, JSON, and more
- **Professional Analysis**: Integration with industry-standard tools (Pylint, ESLint, TypeScript compiler, etc.)
- **Detailed Metrics**: Cyclomatic complexity, maintainability index, Halstead metrics, and code quality scores
- **Security Analysis**: Built-in security vulnerability detection
- **Modern Web Interface**: Clean, responsive UI with real-time analysis
- **REST API**: FastAPI-based backend for programmatic access
- **Export Options**: Generate reports in PDF, HTML, and JSON formats

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js 14+ (optional, for enhanced JavaScript/TypeScript analysis)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-code-reviewer.git
cd ai-code-reviewer
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create necessary package files:
```bash
touch backend/__init__.py
touch analysis/__init__.py
```

4. Start the server:
```bash
python direct_server.py
```

5. Open your browser and navigate to `http://localhost:8001`

### Optional Enhanced Analysis Tools

For comprehensive analysis, install language-specific tools:

```bash
# JavaScript/TypeScript
npm install -g eslint typescript tslint

# Python (additional tools)
pip install black isort safety

# Java tools (download separately)
# - CheckStyle: https://checkstyle.sourceforge.io/
# - PMD: https://pmd.github.io/
# - SpotBugs: https://spotbugs.github.io/

# C/C++ tools
# Linux: sudo apt-get install cppcheck clang-tidy
# macOS: brew install cppcheck llvm
```

## Usage

### Web Interface

1. Paste your code into the editor or load a file
2. Click "Run Analysis" to get comprehensive feedback
3. Review issues, complexity metrics, and suggestions
4. Export reports in your preferred format

### API Usage

```python
import requests

# Analyze code via API
response = requests.post('http://localhost:8001/analyze/', json={
    'code': 'def hello():\n    print("Hello, World!")',
    'filename': 'example.py'
})

result = response.json()
print(f"Score: {result['analysis']['score']}/100")
```

### Command Line Interface

```bash
# Analyze a single file
python main.py path/to/your/file.py

# Analyze a directory
python main.py path/to/your/project/

# Generate reports
python main.py path/to/code --output reports/
```

## Supported Languages

| Language | Syntax Check | Complexity | Style | Security | Tools Used |
|----------|--------------|------------|-------|----------|------------|
| Python | ✅ | ✅ | ✅ | ✅ | Pylint, Flake8, MyPy, Bandit |
| JavaScript | ✅ | ✅ | ✅ | ⚠️ | ESLint, Esprima |
| TypeScript | ✅ | ✅ | ✅ | ⚠️ | TSC, ESLint, TSLint |
| Java | ✅ | ✅ | ✅ | ⚠️ | javac, CheckStyle, PMD |
| C/C++ | ✅ | ⚠️ | ⚠️ | ⚠️ | GCC, Clang, cppcheck |
| C# | ✅ | ⚠️ | ⚠️ | ⚠️ | CSC, Roslyn |
| Go | ✅ | ⚠️ | ✅ | ⚠️ | go build, gofmt |
| Rust | ✅ | ⚠️ | ✅ | ⚠️ | rustc, clippy |
| PHP | ✅ | ⚠️ | ⚠️ | ⚠️ | php -l |
| HTML | ✅ | ❌ | ✅ | ❌ | HTML Parser |
| CSS | ✅ | ❌ | ✅ | ❌ | CSS Parser |
| JSON | ✅ | ❌ | ❌ | ❌ | JSON Parser |

Legend: ✅ Full Support, ⚠️ Basic Support, ❌ Not Applicable

## Project Structure

```
ai-code-reviewer/
├── analysis/                 # Core analysis engine
│   ├── analyzer.py          # Main analysis orchestrator
│   ├── error_checker.py     # Language-specific checkers
│   ├── language_detector.py # Multi-language detection
│   └── report_generator.py  # Report generation
├── backend/                 # FastAPI server
│   └── app.py              # API endpoints
├── frontend/               # Web interface
│   └── app.py             # PyQt6 desktop app
├── tests/                 # Test suite
├── examples/              # Usage examples
├── direct_server.py       # Simple server launcher
├── main.py               # CLI interface
└── requirements.txt      # Dependencies
```

## Configuration

### Environment Variables

```bash
# API Configuration
AI_REVIEWER_API=http://127.0.0.1:8001
ANALYSIS_TIMEOUT=30

# Tool Paths (optional)
PYLINT_PATH=/usr/local/bin/pylint
ESLINT_PATH=/usr/local/bin/eslint
```

### Analysis Settings

Create `config.json` to customize analysis behavior:

```json
{
  "analysis": {
    "complexity_threshold": 10,
    "line_length_limit": 120,
    "enable_security_checks": true,
    "enable_type_checking": true
  },
  "scoring": {
    "issue_penalties": {
      "critical": 15,
      "high": 8,
      "medium": 4,
      "low": 2
    }
  }
}
```

## API Reference

### Endpoints

#### `POST /analyze/`
Analyze code and return comprehensive results.

**Request Body:**
```json
{
  "code": "string",
  "filename": "string (optional)"
}
```

**Response:**
```json
{
  "analysis": {
    "language": "python",
    "score": 85.5,
    "grade": "B+",
    "issues": [...],
    "complexity": [...],
    "quality_metrics": {...},
    "suggestions": [...]
  }
}
```

#### `GET /`
Health check endpoint.

## Development

### Setting Up Development Environment

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements.txt
pip install pytest black flake8 mypy
```

4. Run tests:
```bash
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Ensure code quality: `black . && flake8 . && mypy .`
5. Run the test suite: `pytest`
6. Commit your changes: `git commit -am 'Add feature'`
7. Push to the branch: `git push origin feature-name`
8. Submit a Pull Request

### Code Style

This project follows:
- PEP 8 for Python code
- ESLint standards for JavaScript/TypeScript
- Consistent naming conventions across languages
- Comprehensive docstrings and type hints

## Performance

### Benchmarks

| Language | File Size | Analysis Time | Memory Usage |
|----------|-----------|---------------|--------------|
| Python | 1000 LOC | ~2.3s | ~45MB |
| JavaScript | 1000 LOC | ~1.8s | ~38MB |
| Java | 1000 LOC | ~3.1s | ~52MB |

### Optimization Tips

- Use file-based analysis for large codebases
- Enable caching for repeated analysis
- Consider parallel processing for multiple files
- Limit scope of security analysis for performance-critical scenarios

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/yourusername/ai-code-reviewer/issues)
- **Documentation**: Full documentation available at [docs/](docs/)
- **Community**: Join discussions in [GitHub Discussions](https://github.com/yourusername/ai-code-reviewer/discussions)

## Roadmap

### Version 2.0 (Planned)
- [ ] Real-time collaborative analysis
- [ ] Integration with popular IDEs (VS Code, IntelliJ)
- [ ] Machine learning-based suggestion improvements
- [ ] Support for additional languages (Ruby, Scala, Kotlin)
- [ ] Advanced security vulnerability database
- [ ] Cloud deployment options

### Version 1.1 (In Progress)
- [ ] Improved Docker support
- [ ] Enhanced reporting templates
- [ ] Batch processing capabilities
- [ ] Integration with CI/CD pipelines

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- Analysis powered by [Pylint](https://pylint.org/), [ESLint](https://eslint.org/), and other industry-standard tools
- Complexity metrics based on [Radon](https://radon.readthedocs.io/) library
- Security analysis using [Bandit](https://bandit.readthedocs.io/)

---

**Made with ❤️ by developers, for developers**
