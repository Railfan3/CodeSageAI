import os

def bad_func(x):
    for i in range(len(x)):
        print(i)


"""This is a test file for the AI Code Reviewer project."""

def greet(name: str) -> str:
    """Return a greeting message for the given name."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("Mukul"))
