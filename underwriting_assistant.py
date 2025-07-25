import json
from collections import defaultdict
from pathlib import Path

LOG_PATH = Path(__file__).parent / "logs" / "underwriting_data.jsonl"

def analyze_logs():
    scores = []
    field_frequency = defaultdict(int)
    field_weights = defaultdict(float)

    with open(LOG_PATH, 'r') as f:
        for line in f:
            entry = json.loads(line)
            input_data = entry.get("input", {})
            score_data = entry.get("score", {}).get("total_score", 0)
            scores.append(score_data)

            for field, value in input_data.items():
                if isinstance(value, (int, float)):
                    field_weights[field] += float(value)
                elif isinstance(value, str) and value.strip():
                    field_frequency[field] += 1

    avg_score = round(sum(scores) / len(scores), 2) if scores else 0
    top_fields = sorted(field_frequency.items(), key=lambda x: x[1], reverse=True)[:10]

    print("✅ ML Assistant Report")
    print("----------------------")
    print(f"Average Score: {avg_score}")
    print("Most Used Fields:")
    for field, freq in top_fields:
        print(f"- {field}: {freq} entries")

    print("Average Raw Contributions (numeric fields):")
    for field, total in field_weights.items():
        print(f"- {field}: {round(total / len(scores), 2) if scores else 0}")

if __name__ == "__main__":
    analyze_logs()
