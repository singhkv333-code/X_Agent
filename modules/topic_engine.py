import os
import json
import random

class TopicEngine:
    def __init__(self):
        self.calendar_file = "data/content_calendar.json"
        
        # Initial pool of IB topic seeds
        self.topic_pool = [
            {"topic": "DCF Valuation basics", "category": "Technical"},
            {"topic": "LBO modeling for beginners", "category": "Technical"},
            {"topic": "M&A deal flow in 2026", "category": "News"},
            {"topic": "How to network with Analysts", "category": "Career"},
            {"topic": "The 'Walk me through a DCF' question", "category": "Interview"},
            {"topic": "Difference between Bulge Bracket and Boutique", "category": "Industry"},
            {"topic": "Explaining EBITDA like I'm five", "category": "Jargon"},
            {"topic": "Day in the life of an IB Associate", "category": "Career"},
            {"topic": "Why buy-side is different from sell-side", "category": "Industry"},
            {"topic": "Common technical interview pitfalls", "category": "Interview"},
            {"topic": "Understanding the Pitch Book structure", "category": "Work product"},
            {"topic": "The importance of the CIM in a deal", "category": "Jargon"},
            {"topic": "Leverage ratios explained", "category": "Technical"},
            {"topic": "Public Comps vs Precedent Transactions", "category": "Technical"},
            {"topic": "Investment Banking exit opportunities", "category": "Career"}
        ]
        
        self.load_calendar()

    def load_calendar(self):
        if os.path.exists(self.calendar_file):
            with open(self.calendar_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        else:
            self.history = []

    def save_calendar(self):
        with open(self.calendar_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=4)

    def get_daily_topic(self):
        # Filter out recently used topics
        used_topics = {h['topic'] for h in self.history[-10:]} # Don't repeat last 10
        available_topics = [t for t in self.topic_pool if t['topic'] not in used_topics]
        
        if not available_topics:
            # If we somehow ran out of unique topics, reset or pick random
            available_topics = self.topic_pool

        topic_entry = random.choice(available_topics)
        return topic_entry

    def log_topic(self, topic_entry):
        from datetime import datetime
        self.history.append({
            "topic": topic_entry['topic'],
            "category": topic_entry['category'],
            "timestamp": datetime.now().isoformat()
        })
        self.save_calendar()

    def add_custom_topic(self, topic, category="Custom"):
        self.topic_pool.append({"topic": topic, "category": category})
        return f"Added custom topic: {topic}"

if __name__ == "__main__":
    engine = TopicEngine()
    topic = engine.get_daily_topic()
    print(f"Today's Topic: {topic['topic']} ({topic['category']})")
    engine.log_topic(topic)
