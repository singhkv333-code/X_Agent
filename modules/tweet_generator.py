import os
import json
from modules.claude_engine import ask_claude

THREAD_DELIMITER = "|||THREAD|||"


def _load_style_instruction() -> str:
    style_file = "data/style_profile.json"
    if os.path.exists(style_file):
        with open(style_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("system_instruction", "")
    return ""


def _parse_tweet(raw: str) -> dict:
    """Parse Claude's raw output into a candidate dict."""
    parts = [p.strip() for p in raw.split(THREAD_DELIMITER) if p.strip()]
    if len(parts) > 1:
        return {"text": parts, "is_thread": True}
    return {"text": parts[0] if parts else raw.strip(), "is_thread": False}


class TweetGenerator:
    def __init__(self, config):
        self.config = config
        self.tweet_structure = config.get("tweet_structure", "")

    def _system_instruction(self) -> str:
        style = _load_style_instruction()
        parts = [self.tweet_structure]
        if style:
            parts.append(f"\nAdditional style notes:\n{style}")
        return "\n".join(parts).strip()

    def generate_from_prompt(self, user_prompt: str) -> dict:
        """Generate a single tweet (or thread) from a user-supplied prompt."""
        system = self._system_instruction()
        raw = ask_claude(user_prompt, system_instruction=system)
        return _parse_tweet(raw)

    def generate_candidates(self, topic_entry: dict) -> list:
        """Generate multiple candidates for the auto-pilot pipeline."""
        system = self._system_instruction()
        num = self.config.get("posting", {}).get("candidates_per_day", 5)

        prompt = (
            f"Generate {num} different tweet candidates about: {topic_entry['topic']} "
            f"(Category: {topic_entry['category']}).\n\n"
            f"For each candidate:\n"
            f"- Write the tweet text following all rules.\n"
            f"- If it's a thread, separate parts with {THREAD_DELIMITER}\n"
            f"- Separate each candidate with ===CANDIDATE===\n\n"
            f"Output ONLY the candidates separated by ===CANDIDATE===. No numbering, no labels."
        )

        raw = ask_claude(prompt, system_instruction=system)
        raw_candidates = [c.strip() for c in raw.split("===CANDIDATE===") if c.strip()]

        candidates = []
        for raw_c in raw_candidates:
            c = _parse_tweet(raw_c)
            c["rationale"] = ""
            candidates.append(c)

        return candidates


if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    gen = TweetGenerator(cfg)
    result = gen.generate_from_prompt("Explain what a DCF valuation is for someone new to IB.")
    print(result)
