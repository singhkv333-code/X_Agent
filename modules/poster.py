import os
import json
import tweepy
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class Poster:
    def __init__(self):
        self.log_file = "data/posted_tweets.json"
        
        # Twitter API Keys
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
        self.client = None
        if all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            try:
                self.client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_secret
                )
            except Exception as e:
                print(f"Error initializing Twitter Client: {e}")

    def post(self, candidate, topic_entry):
        if not self.client:
            return {"status": "error", "message": "Twitter API keys not configured. Post failed."}

        try:
            tweet_ids = []
            if candidate["is_thread"]:
                # Post thread
                previous_id = None
                for part in candidate["text"]:
                    response = self.client.create_tweet(text=part, in_reply_to_tweet_id=previous_id)
                    previous_id = response.data['id']
                    tweet_ids.append(previous_id)
            else:
                # Post single tweet
                response = self.client.create_tweet(text=candidate["text"])
                tweet_ids.append(response.data['id'])
            
            self.log_post(candidate, topic_entry, tweet_ids)
            return {"status": "success", "tweet_ids": tweet_ids}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def log_post(self, candidate, topic_entry, tweet_ids):
        history = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        history.append({
            "timestamp": datetime.now().isoformat(),
            "topic": topic_entry["topic"],
            "tweet_text": candidate["text"],
            "is_thread": candidate["is_thread"],
            "tweet_ids": tweet_ids
        })
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4)

if __name__ == "__main__":
    # Test logging (wont post without real keys)
    poster = Poster()
    mock_candidate = {"text": "Testing the logger...", "is_thread": False}
    mock_topic = {"topic": "Test", "category": "Internal"}
    # poster.log_post(mock_candidate, mock_topic, ["12345"])
    print("Poster initialized.")
