import os
import json
import tweepy
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

IST = timezone(timedelta(hours=5, minutes=30))


class Poster:
    def __init__(self):
        self.log_file = "data/posted_tweets.json"

        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

        self.client = None   # Tweepy v2 — for create_tweet
        self.api_v1 = None   # Tweepy v1.1 — for media_upload

        if all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            try:
                # v2 client
                self.client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_secret,
                )
                # v1.1 API for media upload (v2 doesn't support it directly)
                auth = tweepy.OAuth1UserHandler(
                    self.api_key, self.api_secret,
                    self.access_token, self.access_secret,
                )
                self.api_v1 = tweepy.API(auth)
            except Exception as e:
                print(f"Error initializing Twitter clients: {e}")

    def _upload_media(self, image_path: str) -> str | None:
        """Upload image via v1.1 API and return media_id string."""
        if not self.api_v1 or not image_path or not os.path.exists(image_path):
            return None
        try:
            media = self.api_v1.media_upload(filename=image_path)
            return str(media.media_id)
        except Exception as e:
            print(f"Warning: media upload failed — {e}")
            return None

    def post(self, candidate: dict, topic_entry: dict,
             user_prompt: str = "", image_info: dict | None = None) -> dict:
        if not self.client:
            return {"status": "error", "message": "Twitter API keys not configured."}

        # Upload image once (attach to first tweet only)
        media_id = None
        if image_info and image_info.get("local_path"):
            media_id = self._upload_media(image_info["local_path"])
            if not media_id:
                print("Warning: proceeding without image.")

        try:
            tweet_ids = []
            if candidate["is_thread"]:
                previous_id = None
                for i, part in enumerate(candidate["text"]):
                    kwargs = {"text": part, "in_reply_to_tweet_id": previous_id}
                    if i == 0 and media_id:
                        kwargs["media_ids"] = [media_id]
                    response = self.client.create_tweet(**kwargs)
                    previous_id = response.data["id"]
                    tweet_ids.append(previous_id)
            else:
                kwargs = {"text": candidate["text"]}
                if media_id:
                    kwargs["media_ids"] = [media_id]
                response = self.client.create_tweet(**kwargs)
                tweet_ids.append(response.data["id"])

            self._log(candidate, topic_entry, tweet_ids, user_prompt, image_info)
            return {"status": "success", "tweet_ids": tweet_ids}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _log(self, candidate: dict, topic_entry: dict, tweet_ids: list,
             user_prompt: str = "", image_info: dict | None = None):
        history = []
        if os.path.exists(self.log_file):
            with open(self.log_file, "r", encoding="utf-8") as f:
                history = json.load(f)

        history.append({
            "timestamp": datetime.now(IST).isoformat(),
            "user_prompt": user_prompt,
            "generated_tweet": candidate["text"],
            "is_thread": candidate["is_thread"],
            "image_query": image_info.get("query") if image_info else None,
            "image_source_url": image_info.get("source_url") if image_info else None,
            "image_local_path": image_info.get("local_path") if image_info else None,
            "tweet_ids": [str(t) for t in tweet_ids],
            "mode": "interactive" if user_prompt else "autopilot",
            "topic": topic_entry.get("topic"),
        })

        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)


if __name__ == "__main__":
    poster = Poster()
    print("Poster initialized. v1.1 API available:", poster.api_v1 is not None)
