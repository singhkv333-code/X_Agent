import json
from modules.claude_engine import ask_claude_json


class Ranker:
    def __init__(self, config):
        self.config = config

    def rank_candidates(self, candidates: list, topic_entry: dict) -> list:
        guidelines = self.config.get("guidelines", [])
        guidelines_str = "\n".join(f"- {g}" for g in guidelines)

        prompt = (
            f"Rate the following tweet candidates for an Investment Banking audience.\n\n"
            f"TOPIC: {topic_entry['topic']}\n"
            f"GUIDELINES:\n{guidelines_str}\n\n"
            f"CANDIDATES:\n{json.dumps(candidates, indent=2)}\n\n"
            f"TASK:\n"
            f"Rank these candidates based on:\n"
            f"1. Engagement potential (hook strength, clarity)\n"
            f"2. Adherence to guidelines\n"
            f"3. Educational value for students/career-switchers\n\n"
            f"Return the list of candidates sorted by rank (best first), "
            f"adding a \"score\" (1-10) and \"feedback\" key to each.\n"
            f"Return as a JSON list only."
        )

        return ask_claude_json(prompt)


if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    ranker = Ranker(cfg)
    mock_candidates = [
        {"text": "IB is hard. Do a DCF.", "is_thread": False, "rationale": "Short"},
        {"text": "Here is why DCF is the heartbeat of M&A...", "is_thread": True, "rationale": "Educational"}
    ]
    mock_topic = {"topic": "DCF basics", "category": "Technical"}
    print(ranker.rank_candidates(mock_candidates, mock_topic))
