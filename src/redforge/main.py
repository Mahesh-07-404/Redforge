import typer
from rich import print as rprint
from .session.store import SessionStore
from .session.manager import SessionManager
from .core.langgraph_agent import RedForgeAgent
from .core.config import get_settings
import asyncio

app = typer.Typer(help="RedForge - Autonomous Penetration Testing Agent")

@app.command()
def run(
    mode: str = typer.Option("bugbounty", "--mode", "-m", help="Operational mode"),
    target: str = typer.Option("", "--target", "-t", help="Target domain/IP"),
    autonomy: str = typer.Option("manual", "--autonomy", "-a", help="Autonomy level (manual, partial, full)"),
):
    """Main CLI entry point for RedForge using Typer."""
    rprint(f"[bold red]RedForge[/bold red] started in [cyan]{mode}[/cyan] mode.")
    
    store = SessionStore()
    session_manager = SessionManager(store)
    session = session_manager.create(mode, target, autonomy)
    
    rprint(f"Session created: [green]{session.id}[/green]")
    
    settings = get_settings()
    agent = RedForgeAgent(config=settings, llm_provider=settings.llm.provider, model=settings.llm.model)
    
    rprint("Agent initialized successfully.")

if __name__ == "__main__":
    app()
