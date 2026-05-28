import asyncio
import sys
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from sidekick import Sidekick

console = Console()

async def main():
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]🤖 AI Sidekick Terminal[/bold cyan]\n"
        "[dim]Powered by Claude 4.6 Sonnet (via OpenRouter)[/dim]",
        border_style="cyan"
    ))
    
    sidekick = Sidekick()
    
    with console.status("[bold yellow]Initializing Sidekick tools and browser...[/bold yellow]", spinner="point"):
        await sidekick.setup()
    
    console.print("[bold green]✓ Ready![/bold green] Type [bold red]'exit'[/bold red] to quit.\n")
    
    history = []
    
    try:
        while True:
            # Get user input
            user_input = Prompt.ask("\n[bold magenta]You[/bold magenta]")
            
            if user_input.strip().lower() in ['exit', 'quit']:
                console.print("[dim]Shutting down Sidekick... Goodbye![/dim]\n")
                break
                
            if not user_input.strip():
                continue

            with console.status("[bold cyan]Sidekick is thinking...[/bold cyan]", spinner="dots"):
                # Run the superstep and update the history
                history = await sidekick.run_superstep(
                    message=user_input, 
                    success_criteria="Complete the user's request thoroughly.", 
                    history=history
                )
            
            # The history contains dictionaries with 'role' and 'content'
            # We want to grab the latest assistant response
            if history and len(history) > 0:
                latest_response = history[-1].get('content', '')
                
                # Print the response nicely using Rich's Markdown rendering
                console.print("\n[bold blue]Sidekick:[/bold blue]")
                console.print(Panel(Markdown(latest_response), border_style="blue"))
                
    except KeyboardInterrupt:
        console.print("\n[dim]Force quitting...[/dim]")
    finally:
        with console.status("[dim]Cleaning up resources...[/dim]"):
            sidekick.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
