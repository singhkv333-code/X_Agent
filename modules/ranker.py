import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class Ranker:
    def __init__(self, config):
        self.config = config
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(config["gemini"]["model"])

    def rank_candidates(self, candidates, topic_entry):
        guidelines = self.config.get("guidelines", [])
        guidelines_str = "\n".join(f"- {g}" for g in guidelines)

        prompt = f"""
        Rate the following tweet candidates for an Investment Banking audience.
        
        TOPIC: {topic_entry['topic']}
        GUIDELINES:
        {guidelines_str}

        CANDIDATES:
        {json.dumps(candidates, indent=2)}

        TASK:
        Rank these candidates based on:
        1. Engagement potential (hook strength, clarity)
        2. Adherence to guidelines
        3. Educational value for students/career-switchers
        
        Return the list of candidates sorted by rank (best first), adding a "score" (1-10) and "feedback" key to each.
        Return as a JSON list.
        """

        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        
        ranked = json.loads(response.text)
        return ranked

if __name__ == "__main__":
    # Mock test
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
