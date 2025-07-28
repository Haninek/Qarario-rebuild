import json
from collections import defaultdict
from pathlib import Path

LOG_PATH = Path(__file__).parent / "logs" / "underwriting_data.jsonl"


def analyze_logs():
    scores = []
    field_frequency = defaultdict(int)
    field_averages = defaultdict(float)

    try:
        with open(LOG_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    try:
                        entry = json.loads(line)
                        input_data = entry.get("input", {})
                        score = entry.get("score", {}).get("total_score", 0)
                        scores.append(score)
                        
                        for key, val in input_data.items():
                            if isinstance(val, (int, float)):
                        field_averages[key] += float(val)
                    elif isinstance(val, str) and val.strip():
                        field_frequency[key] += 1
    except FileNotFoundError:
        return "No log data found."

    output = []
    output.append("📊 UNDERWRITING ASSISTANT REPORT")
    output.append("-" * 40)
    output.append(f"Total Entries: {len(scores)}")
    output.append(
        f"Average Score: {round(sum(scores)/len(scores), 2) if scores else 0}")
    output.append("\nMost Active Fields (String):")
    for field, count in sorted(field_frequency.items(),
                               key=lambda x: x[1],
                               reverse=True)[:10]:
        output.append(f"- {field}: {count} times")

    output.append("\nAverage Values (Numeric):")
    for field, total in field_averages.items():
        output.append(f"- {field}: {round(total/len(scores), 2)}")

    return "\n".join(output)
