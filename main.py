import sys
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

from modules.style_learner import StyleLearner
from modules.topic_engine import TopicEngine
from modules.tweet_generator import TweetGenerator
from modules.ranker import Ranker
from modules.poster import Poster
from modules.image_fetcher import fetch_image_for_tweet

console = Console()


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


# ─────────────────────────────────────────────────────────────
# Interactive tweet command
# ─────────────────────────────────────────────────────────────

def _format_tweet_preview(candidate: dict) -> str:
    if candidate["is_thread"]:
        return "\n\n".join(
            f"[bold cyan][{i+1}/{len(candidate['text'])}][/bold cyan] {part}"
            for i, part in enumerate(candidate["text"])
        )
    return candidate["text"]


def interactive_tweet():
    config = load_config()
    generator = TweetGenerator(config)
    poster = Poster()

    console.print(Panel(
        "[bold white]IB Tweet Agent — Interactive Mode[/bold white]",
        border_style="blue",
        padding=(0, 2),
    ))

    user_prompt = Prompt.ask("\n[bold]What should the tweet be about?[/bold] Be as detailed as you want\n")

    while True:
        with console.status("[bold yellow]Claude is thinking...[/bold yellow]", spinner="dots"):
            candidate = generator.generate_from_prompt(user_prompt)

        tweet_preview = _format_tweet_preview(candidate)
        console.print()
        console.rule("[bold]Generated Tweet[/bold]")
        console.print(tweet_preview)
        console.rule()

        # Image fetch
        image_info = None
        tweet_text_flat = (
            " ".join(candidate["text"]) if candidate["is_thread"] else candidate["text"]
        )
        with console.status("[bold yellow]Fetching image...[/bold yellow]", spinner="dots"):
            try:
                image_info = fetch_image_for_tweet(tweet_text_flat)
            except Exception as e:
                console.print(f"[dim]Image fetch skipped: {e}[/dim]")

        if image_info:
            console.print(
                f"\n[green]Image fetched:[/green] {image_info['local_path']}\n"
                f"[dim]Source: {image_info['source_url']}[/dim]"
            )
        else:
            console.print("\n[dim]No image found — will post text only.[/dim]")

        console.print(
            "\n[bold cyan]\\[y][/bold cyan] Post  "
            "[bold red]\\[n][/bold red] Cancel  "
            "[bold yellow]\\[r][/bold yellow] Regenerate  "
            "[bold magenta]\\[e][/bold magenta] Edit prompt"
        )
        choice = Prompt.ask("", choices=["y", "n", "r", "e"], default="n")

        if choice == "y":
            topic_entry = {"topic": user_prompt[:80], "category": "Interactive"}
            with console.status("[bold green]Posting to X...[/bold green]", spinner="dots"):
                result = poster.post(
                    candidate,
                    topic_entry,
                    user_prompt=user_prompt,
                    image_info=image_info,
                )
            if result["status"] == "success":
                console.print(f"[bold green]Posted! Tweet IDs: {result['tweet_ids']}[/bold green]")
            else:
                console.print(f"[bold red]Post failed: {result['message']}[/bold red]")
            break

        elif choice == "n":
            console.print("[dim]Cancelled.[/dim]")
            break

        elif choice == "r":
            console.print("[yellow]Regenerating...[/yellow]")
            # Loop back with same prompt

        elif choice == "e":
            user_prompt = Prompt.ask("\n[bold]New/modified prompt[/bold]")


# ─────────────────────────────────────────────────────────────
# Auto-pilot pipeline (run / dry-run)
# ─────────────────────────────────────────────────────────────

class IBTweetAgent:
    def __init__(self):
        self.config = load_config()
        self.learner = StyleLearner(self.config)
        self.topic_engine = TopicEngine()
        self.generator = TweetGenerator(self.config)
        self.ranker = Ranker(self.config)
        self.poster = Poster()

    def run_pipeline(self, dry_run=True):
        console.print("[bold blue]Starting IB Tweet Agent Pipeline...[/bold blue]")

        topic = self.topic_engine.get_daily_topic()
        console.print(f"[green]Today's Topic:[/green] {topic['topic']} ({topic['category']})")

        console.print("[yellow]Generating tweet candidates...[/yellow]")
        candidates = self.generator.generate_candidates(topic)

        console.print("[yellow]Ranking candidates...[/yellow]")
        ranked = self.ranker.rank_candidates(candidates, topic)

        table = Table(title=f"Candidates for: {topic['topic']}", box=box.SIMPLE)
        table.add_column("Rank", style="cyan", width=6)
        table.add_column("Score", style="magenta", width=7)
        table.add_column("Tweet Preview", style="white")

        for i, c in enumerate(ranked, 1):
            preview = c["text"] if not c["is_thread"] else f"[Thread] {c['text'][0]}..."
            if isinstance(preview, str) and len(preview) > 100:
                preview = preview[:97] + "..."
            table.add_row(str(i), str(c.get("score", "N/A")), preview)

        console.print(table)

        if dry_run:
            console.print("[bold cyan]Dry-run complete. No tweets were posted.[/bold cyan]")
            return ranked

        best = ranked[0]
        auto_post = self.config.get("posting", {}).get("auto_post", False)

        if auto_post:
            # Fetch image for best candidate
            image_info = None
            tweet_text_flat = (
                " ".join(best["text"]) if best["is_thread"] else best["text"]
            )
            with console.status("[yellow]Fetching image...[/yellow]", spinner="dots"):
                try:
                    image_info = fetch_image_for_tweet(tweet_text_flat)
                except Exception as e:
                    console.print(f"[dim]Image fetch skipped: {e}[/dim]")

            console.print("[bold green]Posting the best candidate to X...[/bold green]")
            result = self.poster.post(best, topic, image_info=image_info)
            if result["status"] == "success":
                console.print(f"[bold green]Posted! Tweet IDs: {result['tweet_ids']}[/bold green]")
                self.topic_engine.log_topic(topic)
            else:
                console.print(f"[bold red]Posting failed: {result['message']}[/bold red]")
        else:
            console.print("[yellow]auto_post is disabled in config.yaml. Skipping post.[/yellow]")

        return ranked


# ─────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────

def print_help():
    console.print("""
[bold]Usage:[/bold] python main.py [command]

[bold]Commands:[/bold]
  [cyan]tweet[/cyan]      Interactive: type a prompt, get a tweet, post it
  [cyan]run[/cyan]        Auto-pilot: generate & post (if auto_post is true)
  [cyan]dry-run[/cyan]    Auto-pilot: generate & rank without posting
  [cyan]learn[/cyan]      Extract style patterns from data/example_tweets.txt
  [cyan]status[/cyan]     Show current configuration and history count
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "tweet":
        interactive_tweet()

    elif cmd in ("run", "dry-run"):
        agent = IBTweetAgent()
        agent.run_pipeline(dry_run=(cmd == "dry-run"))

    elif cmd == "learn":
        config = load_config()
        learner = StyleLearner(config)
        console.print("[yellow]Learning style from examples...[/yellow]")
        result = learner.learn_style()
        console.print(f"[green]{result}[/green]")

    elif cmd == "status":
        config = load_config()
        engine = TopicEngine()
        console.print("[bold]Agent Config:[/bold]")
        console.print(f"  Engine: Claude Code CLI (claude --print)")
        console.print(f"  Auto-post: {config['posting']['auto_post']}")
        console.print(f"  History count: {len(engine.history)}")

    else:
        print_help()
