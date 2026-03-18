import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class StyleLearner:
    def __init__(self, config):
        self.config = config
        self.example_file = "data/example_tweets.txt"
        self.profile_file = "data/style_profile.json"
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(config["gemini"]["model"])

    def learn_style(self):
        if not os.path.exists(self.example_file):
            return "No example tweets found in data/example_tweets.txt"

        with open(self.example_file, 'r', encoding='utf-8') as f:
            content = f.read()

        examples = [e.strip() for e in content.split('---') if e.strip()]
        if not examples:
            return "No valid examples found in example_tweets.txt"

        prompt = f"""
        Analyze the following example tweets for writing style, tone, and structure.
        
        EXAMPLES:
        {chr(10).join(f"- {e}" for e in examples)}
        
        Output a detailed "Style Profile" that includes:
        1. Hook style (how the tweets start)
        2. Sentence structure and rhythm
        3. Use of jargon/technical terms vs simple language
        4. Call-to-action (CTA) patterns
        5. Tone keywords (e.g., authoritative, witty, mentoring)
        6. Emoji/Hashtag usage patterns
        
        Also provide a concise "System Instruction" that can be used to guide an AI to write exactly in this style.
        
        Return the result as a JSON object with keys: "analysis" and "system_instruction".
        """

        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        profile_data = json.loads(response.text)
        
        with open(self.profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=4)
            
        return f"Successfully learned style from {len(examples)} examples and saved to {self.profile_file}"

if __name__ == "__main__":
    # For quick testing
    import yaml
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    learner = StyleLearner(cfg)
    print(learner.learn_style())
