import os
import json
from modules.claude_engine import ask_claude_json


class StyleLearner:
    def __init__(self, config):
        self.config = config
        self.example_file = "data/example_tweets.txt"
        self.profile_file = "data/style_profile.json"

    def learn_style(self) -> str:
        if not os.path.exists(self.example_file):
            return "No example tweets found in data/example_tweets.txt"

        with open(self.example_file, "r", encoding="utf-8") as f:
            content = f.read()

        examples = [e.strip() for e in content.split("---") if e.strip() and not e.strip().startswith("#")]
        if not examples:
            return "No valid examples found in example_tweets.txt"

        examples_str = "\n".join(f"- {e}" for e in examples)

        prompt = (
            f"Analyze the following example tweets for writing style, tone, and structure.\n\n"
            f"EXAMPLES:\n{examples_str}\n\n"
            f"Output a detailed Style Profile that includes:\n"
            f"1. Hook style (how the tweets start)\n"
            f"2. Sentence structure and rhythm\n"
            f"3. Use of jargon/technical terms vs simple language\n"
            f"4. Call-to-action (CTA) patterns\n"
            f"5. Tone keywords (e.g., authoritative, witty, mentoring)\n"
            f"6. Emoji/Hashtag usage patterns\n\n"
            f"Also provide a concise \"system_instruction\" that can be used to guide an AI to write "
            f"exactly in this style.\n\n"
            f"Return the result as a JSON object with keys: \"analysis\" and \"system_instruction\"."
        )

        profile_data = ask_claude_json(prompt)

        with open(self.profile_file, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=4)

        return f"Successfully learned style from {len(examples)} examples and saved to {self.profile_file}"


if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    learner = StyleLearner(cfg)
    print(learner.learn_style())
