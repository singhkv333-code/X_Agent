import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class TweetGenerator:
    def __init__(self, config):
        self.config = config
        self.style_file = "data/style_profile.json"
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(config["gemini"]["model"])

    def load_style_prompt(self):
        if os.path.exists(self.style_file):
            with open(self.style_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("system_instruction", "")
        return "Write tweet in a professional and engaging way tailored for students interested in Investment Banking."

    def generate_candidates(self, topic_entry):
        style_instruction = self.load_style_prompt()
        guidelines = self.config.get("guidelines", [])
        
        guidelines_str = "\n".join(f"- {g}" for g in guidelines)
        
        num_candidates = self.config.get("posting", {}).get("candidates_per_day", 3)

        prompt = f"""
        {style_instruction}

        TOPIC FOR TODAY: {topic_entry['topic']}
        CATEGORY: {topic_entry['category']}

        CONTENT GUIDELINES:
        {guidelines_str}

        TASK:
        Generate {num_candidates} different tweet candidates based on the topic and category.
        One of the candidates should be a short thread (2-3 parts) if the topic allows for it.
        
        FORMAT:
        Return a JSON list of objects. Each object should have:
        - "text": The tweet text (or list of texts if it's a thread)
        - "is_thread": Boolean
        - "rationale": Why this tweet works for the target audience
        
        Ensure each tweet is under 280 characters.
        STRICT REQUIREMENT: NEVER use emojis, icons, or any non-text symbols in the tweets.
        """

        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=self.config["gemini"].get("temperature", 1.0),
                response_mime_type="application/json"
            )
        )
        
        candidates = json.loads(response.text)
        return candidates

if __name__ == "__main__":
    # Quick test
    import yaml
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    
    # Mock topic
    mock_topic = {"topic": "The importance of M&A in IB", "category": "General"}
    
    generator = TweetGenerator(cfg)
    # Note: This requires data/style_profile.json to exist if you want style learning
    candidates = generator.generate_candidates(mock_topic)
    
    print(f"Generated {len(candidates)} candidates:")
    for i, c in enumerate(candidates, 1):
        print(f"\nCandidate {i}:")
        if c["is_thread"]:
            for part in c["text"]:
                print(f"  - {part}")
        else:
            print(f"  {c['text']}")
        print(f"  Rationale: {c['rationale']}")
