# ai_code_reviewer/analysis/suggestions.py

def generate_suggestions(issues):
    """Generate human-friendly suggestions from analysis issues."""

    suggestions = []

    if not issues:
        return ["Code looks clean and well-structured. ✅"]

    for issue in issues:
        msg_id = issue.get("message-id", "")
        msg = issue.get("message", "")

        if msg_id.startswith("C"):
            suggestions.append("Follow PEP8 conventions for cleaner code.")
        elif msg_id.startswith("E"):
            suggestions.append(f"Fix error: {msg}")
        elif msg_id.startswith("W"):
            suggestions.append("Consider improving code readability.")
        elif msg_id.startswith("R"):
            suggestions.append("Refactor code for better maintainability.")
        else:
            suggestions.append(f"Review issue: {msg}")

    return list(set(suggestions))  # remove duplicates
