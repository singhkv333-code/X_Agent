import sys
import yaml
import os
from rich.console import Console
from rich.table import Table
from modules.style_learner import StyleLearner
from modules.topic_engine import TopicEngine
from modules.tweet_generator import TweetGenerator
from modules.ranker import Ranker
from modules.poster import Poster

console = Console()

class IBTweetAgent:
    def __init__(self):
        with open("config.yaml", "r") as f:
            self.config = yaml.safe_load(f)
        
        self.learner = StyleLearner(self.config)
        self.topic_engine = TopicEngine()
        self.generator = TweetGenerator(self.config)
        self.ranker = Ranker(self.config)
        self.poster = Poster()

    def run_pipeline(self, dry_run=True):
        console.print("[bold blue]Starting IB Tweet Agent Pipeline...[/bold blue]")
        
        # 1. Topic Selection
        topic = self.topic_engine.get_daily_topic()
        console.print(f"[green]Today's Topic:[/green] {topic['topic']} ({topic['category']})")
        
        # 2. Generation
        console.print("[yellow]Generating tweet candidates...[/yellow]")
        candidates = self.generator.generate_candidates(topic)
        
        # 3. Ranking
        console.print("[yellow]Ranking candidates...[/yellow]")
        ranked_candidates = self.ranker.rank_candidates(candidates, topic)
        
        # Display Results
        table = Table(title=f"Candidates for: {topic['topic']}")
        table.add_column("Rank", style="cyan")
        table.add_column("Score", style="magenta")
        table.add_column("Tweet Preview", style="white")
        
        for i, c in enumerate(ranked_candidates, 1):
            preview = c['text'] if not c['is_thread'] else f"[Thread] {c['text'][0]}..."
            table.add_row(str(i), str(c.get('score', 'N/A')), preview)
        
        console.print(table)
        
        if dry_run:
            console.print("[bold cyan]Dry-run complete. No tweets were posted.[/bold cyan]")
            return ranked_candidates
        
        # 4. Posting (Top 1)
        best_candidate = ranked_candidates[0]
        auto_post = self.config.get("posting", {}).get("auto_post", False)
        
        if auto_post:
            console.print("[bold green]Posting the best candidate to Twitter...[/bold green]")
            result = self.poster.post(best_candidate, topic)
            if result["status"] == "success":
                console.print(f"[bold green]Posted successfully! Tweet IDs: {result['tweet_ids']}[/bold green]")
                self.topic_engine.log_topic(topic)
            else:
                console.print(f"[bold red]Posting failed: {result['message']}[/bold red]")
        else:
            console.print("[yellow]Auto-post is disabled in config.yaml. Skipping Twitter post.[/yellow]")
            
        return ranked_candidates

def print_help():
    console.print("""
[bold]Usage:[/bold] python main.py [command]

[bold]Commands:[/bold]
  [cyan]run[/cyan]        Run the full pipeline (posts if auto_post is true)
  [cyan]dry-run[/cyan]    Run the pipeline without posting
  [cyan]learn[/cyan]      Extract style patterns from data/example_tweets.txt
  [cyan]status[/cyan]     Show current configuration and history status
    """)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    agent = IBTweetAgent()
    
    if cmd == "run":
        agent.run_pipeline(dry_run=False)
    elif cmd == "dry-run":
        agent.run_pipeline(dry_run=True)
    elif cmd == "learn":
        console.print("[yellow]Learning style from examples...[/yellow]")
        result = agent.learner.learn_style()
        console.print(f"[green]{result}[/green]")
    elif cmd == "status":
        console.print(f"[bold]Agent Config:[/bold]")
        console.print(f"  Model: {agent.config['gemini']['model']}")
        console.print(f"  Auto-post: {agent.config['posting']['auto_post']}")
        console.print(f"  History count: {len(agent.topic_engine.history)}")
    else:
        print_help()
