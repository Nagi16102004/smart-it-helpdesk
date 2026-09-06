# Rule-based priority engine
# NOTE: This is simple if-else business logic, NOT AI or Machine Learning.

def calculate_priority(impact, urgency):
    priority_matrix = {
        ("High", "High"): "P1",
        ("High", "Medium"): "P2",
        ("High", "Low"): "P3",
        ("Medium", "High"): "P2",
        ("Medium", "Medium"): "P3",
        ("Medium", "Low"): "P4",
        ("Low", "High"): "P3",
        ("Low", "Medium"): "P4",
        ("Low", "Low"): "P4",
    }
    return priority_matrix.get((impact, urgency), "P4")