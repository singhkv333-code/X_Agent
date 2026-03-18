# 🤖 IB Tweet Agent

A self-sustaining AI agent that researches, writes, and posts daily tweets about Investment Banking — targeted at students and career-switchers.

## 🚀 Quick Start

### 1. Setup Environment
Ensure you have Python installed. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy `.env.example` to `.env` and paste your keys:
- **GEMINI_API_KEY**: Get it free at [aistudio.google.com](https://aistudio.google.com)
- **Twitter Keys**: Get them at [developer.twitter.com](https://developer.twitter.com) (Free tier is enough)

### 3. Add Example Tweets
Open `data/example_tweets.txt` and paste 5-20 tweets you've written or like. This teaches the AI your tone and structure. Use `---` to separate tweets.

### 4. Extract Style
Run this command to analyze your examples:
```bash
python main.py learn
```

### 5. Dry Run (Test)
Generate 5 candidates without posting:
```bash
python main.py dry-run
```

## 📅 Automation

To run the agent on autopilot:
1. Open `config.yaml` and set `auto_post: true`.
2. Run the scheduler:
```bash
python scheduler.py
```
The agent will now generate and post at the `post_time` specified in `config.yaml` (default 09:00 AM).

## 🛠 Commands

| Command | Description |
|---|---|
| `python main.py learn` | Analyze your style from `data/example_tweets.txt` |
| `python main.py dry-run` | Generate and rank tweets (printing results to console) |
| `python main.py run` | Generate and post (only posts if `auto_post` is true) |
| `python main.py status` | Check configuration and history count |
| `python scheduler.py` | Start the 24/7 scheduler loop |

---
**Guidelines**: You can change the AI's behavior (e.g., "Always end with a question", "Never use emojis") in `config.yaml`.
**Topics**: The agent picks from a pool of IB topics in `modules/topic_engine.py` and avoids repeating recent ones.
