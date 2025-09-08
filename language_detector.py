# analysis/language_detector.py
from pygments.lexers import guess_lexer_for_filename, guess_lexer
from pygments.util import ClassNotFound

def detect_language(code: str, filename: str = None) -> str:
    """
    Detect language using pygments. Returns lowercase language name (e.g. 'python', 'javascript', 'c++').
    Falls back to 'unknown'.
    """
    try:
        if filename:
            lexer = guess_lexer_for_filename(filename, code)
        else:
            lexer = guess_lexer(code)
        return lexer.name.lower()
    except ClassNotFound:
        return "unknown"
