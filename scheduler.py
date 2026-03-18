import time
import yaml
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from main import IBTweetAgent
from rich.console import Console

console = Console()

def run_daily_job():
    console.print(f"\n[bold magenta]⏰ Scheduled Job Triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold magenta]")
    try:
        agent = IBTweetAgent()
        agent.run_pipeline(dry_run=False) # This will post if auto_post is True in config
    except Exception as e:
        console.print(f"[bold red]✘ Scheduled job failed: {e}[/bold red]")

def start_scheduler():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    post_time = config.get("schedule", {}).get("post_time", "09:00")
    timezone = config.get("schedule", {}).get("timezone", "Asia/Kolkata")
    
    hour, minute = post_time.split(":")
    
    scheduler = BlockingScheduler(timezone=timezone)
    
    # Schedule the job
    scheduler.add_job(
        run_daily_job,
        CronTrigger(hour=hour, minute=minute),
        name="Daily IB Tweet Post"
    )
    
    console.print(f"[bold green]📅 Scheduler started! Looking for post time: {post_time} ({timezone})[/bold green]")
    console.print("[yellow]Press Ctrl+C to stop the scheduler.[/yellow]")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        console.print("[bold red]Scheduler stopped.[/bold red]")

if __name__ == "__main__":
    start_scheduler()
