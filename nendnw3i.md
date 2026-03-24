# IB Tweet Agent — Project Summary

## What It Is

An automated AI agent that writes and posts daily tweets about **Investment Banking (IB)**, targeting students and career-switchers. Despite the repo being named "Restaurant-Backend", this project has nothing to do with restaurants — it is a Twitter/X automation tool for IB education content.

---

## What It Does (End-to-End)

Every day, the agent runs a 4-step pipeline:

### Step 1 — Pick a Topic (`topic_engine.py`)
- Randomly selects a topic from a built-in pool of 15 IB subjects.
- Categories include: Technical, Career, Interview, Industry, Jargon, Work product, News.
- Example topics: "DCF Valuation basics", "LBO modeling for beginners", "How to network with Analysts".
- Avoids repeating the last 10 used topics by checking `data/content_calendar.json`.

### Step 2 — Generate Tweet Candidates (`tweet_generator.py`)
- Calls **Google Gemini 2.0 Flash** (free tier, 1500 req/day) via the `GEMINI_API_KEY`.
- Generates 5 candidate tweets (configurable) for that day's topic.
- One candidate is always a short **thread** (2–3 parts).
- Applies strict writing guidelines: no emojis, under 260 characters, max 2 hashtags, explain jargon simply, end with a question or CTA.
- Can optionally load a learned style profile from `data/style_profile.json` to match a specific writing voice.

### Step 3 — Rank the Candidates (`ranker.py`)
- Sends all candidates back to Gemini for scoring.
- Scores each tweet 1–10 on: hook strength, guideline adherence, and educational value.
- Returns the list sorted best-first with a score and feedback note per tweet.

### Step 4 — Post to Twitter (`poster.py`)
- Uses **Tweepy** to post via the Twitter API v2.
- Posts the top-ranked candidate only.
- Threads are posted as reply-chains.
- Logs every post to `data/posted_tweets.json` with timestamp, topic, text, and tweet IDs.
- Posting only happens if `auto_post: true` is set in `config.yaml`.

---

## Style Learning (One-Time Setup)

Before running the pipeline, you can teach the agent your writing style:
1. Paste 5–20 example tweets into `data/example_tweets.txt`, separated by `---`.
2. Run `python main.py learn`.
3. Gemini analyzes the examples and saves a style profile to `data/style_profile.json`.
4. All future tweet generation uses this profile as a system instruction.

---

## Scheduling (`scheduler.py`)

Run `python scheduler.py` to keep the agent alive 24/7. It uses **APScheduler** with a cron trigger to fire the full pipeline at a set time every day (default: 09:00 AM IST). The timezone and time are set in `config.yaml`.

---

## File Structure

```
Restaurant-Backend/
├── main.py                  # Entry point + pipeline orchestrator
├── scheduler.py             # 24/7 cron scheduler
├── config.yaml              # All settings (time, guidelines, model, auto_post)
├── requirements.txt         # Python dependencies
├── modules/
│   ├── topic_engine.py      # Topic pool + history tracking
│   ├── tweet_generator.py   # Gemini-powered tweet writer
│   ├── ranker.py            # Gemini-powered tweet scorer
│   ├── poster.py            # Tweepy Twitter poster + logger
│   └── style_learner.py     # Gemini-powered style analyzer
└── data/
    ├── example_tweets.txt   # Your example tweets (manual input)
    ├── style_profile.json   # Auto-generated style profile (after `learn`)
    ├── content_calendar.json# Auto-generated topic history log
    └── posted_tweets.json   # Auto-generated post log
```

---

## Dependencies

| Library | Purpose |
|---|---|
| `google-generativeai` | Gemini API for generation and ranking |
| `tweepy` | Twitter API v2 posting |
| `apscheduler` | Daily cron scheduling |
| `python-dotenv` | Load API keys from `.env` |
| `pyyaml` | Read `config.yaml` |
| `rich` | Colored terminal output |

---

## Required API Keys (in `.env`)

```
GEMINI_API_KEY=...          # From aistudio.google.com (free)
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...
```

---

## CLI Commands

| Command | What it does |
|---|---|
| `python main.py dry-run` | Run full pipeline, print ranked tweets, do NOT post |
| `python main.py run` | Run full pipeline and post (if `auto_post: true`) |
| `python main.py learn` | Analyze `example_tweets.txt` and save style profile |
| `python main.py status` | Show current model, auto_post setting, and topic history count |
| `python scheduler.py` | Start the daily autopilot scheduler |
