"""
Baby MARS CLI
==============

Command-line interface for running and interacting with Baby MARS.

Usage:
    baby-mars serve          # Start API server
    baby-mars chat           # Interactive chat session
    baby-mars birth          # Birth a new person
    baby-mars beliefs        # View/manage beliefs
"""

import os
import sys
import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = typer.Typer(
    name="baby-mars",
    help="Baby MARS - Cognitive Architecture with a Rented Brain",
    add_completion=False,
)

console = Console()


# ============================================================
# SERVE COMMAND
# ============================================================

@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
):
    """Start the Baby MARS API server."""
    console.print(Panel.fit(
        "[bold blue]Baby MARS[/bold blue] API Server",
        subtitle="Cognitive Architecture"
    ))

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]Warning:[/red] ANTHROPIC_API_KEY not set")

    console.print(f"\nStarting server at [cyan]http://{host}:{port}[/cyan]")
    console.print("Press [bold]Ctrl+C[/bold] to stop\n")

    import uvicorn
    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


# ============================================================
# CHAT COMMAND
# ============================================================

@app.command()
def chat(
    name: str = typer.Option("Demo User", "--name", "-n", help="Your name"),
    role: str = typer.Option("Controller", "--role", "-r", help="Your role"),
    industry: str = typer.Option("general", "--industry", "-i", help="Industry"),
):
    """Start an interactive chat session."""

    console.print(Panel.fit(
        "[bold blue]Baby MARS[/bold blue] Interactive Chat",
        subtitle=f"Role: {role} | Industry: {industry}"
    ))

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]Error:[/red] ANTHROPIC_API_KEY not set")
        console.print("Set it with: export ANTHROPIC_API_KEY=sk-...")
        raise typer.Exit(1)

    asyncio.run(_run_chat(name, role, industry))


async def _run_chat(name: str, role: str, industry: str):
    """Run interactive chat session."""
    from .birth.birth_system import quick_birth
    from .cognitive_loop.graph import create_graph_in_memory, invoke_cognitive_loop

    console.print("\n[dim]Birthing cognitive agent...[/dim]")

    # Create graph
    graph = create_graph_in_memory()

    # Quick birth for chat
    state = None
    session_started = False

    console.print("[green]Ready![/green] Type your message or [bold]/quit[/bold] to exit.\n")

    while True:
        try:
            # Get user input
            user_input = console.input("[bold cyan]You:[/bold cyan] ")

            if user_input.strip().lower() in ["/quit", "/exit", "/q"]:
                console.print("\n[dim]Goodbye![/dim]")
                break

            if user_input.strip().lower() == "/help":
                console.print(Panel(
                    "/quit - Exit chat\n"
                    "/beliefs - Show activated beliefs\n"
                    "/mode - Show current supervision mode\n"
                    "/help - Show this help",
                    title="Commands"
                ))
                continue

            if user_input.strip().lower() == "/beliefs":
                if state and state.get("activated_beliefs"):
                    table = Table(title="Activated Beliefs")
                    table.add_column("Statement", style="cyan")
                    table.add_column("Category")
                    table.add_column("Strength")
                    for b in state["activated_beliefs"][:10]:
                        table.add_row(
                            b.get("statement", "")[:50],
                            b.get("category", ""),
                            f"{b.get('strength', 0):.2f}"
                        )
                    console.print(table)
                else:
                    console.print("[dim]No beliefs activated yet[/dim]")
                continue

            if user_input.strip().lower() == "/mode":
                if state:
                    mode = state.get("supervision_mode", "unknown")
                    strength = state.get("belief_strength_for_action", 0)
                    console.print(f"Mode: [bold]{mode}[/bold] (strength: {strength:.2f})")
                else:
                    console.print("[dim]No session yet[/dim]")
                continue

            if not user_input.strip():
                continue

            # Initialize or update state
            if state is None:
                state = quick_birth(name, role, industry, user_input)
                session_started = True
            else:
                state["messages"].append({"role": "user", "content": user_input})
                state["current_turn"] += 1

            # Run cognitive loop with spinner
            with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
                config = {"configurable": {"thread_id": state["thread_id"]}}
                state = await invoke_cognitive_loop(state, graph, config)

            # Display response
            response = state.get("final_response", "")
            mode = state.get("supervision_mode", "")

            # Mode indicator
            mode_colors = {
                "guidance_seeking": "yellow",
                "action_proposal": "blue",
                "autonomous": "green",
            }
            mode_color = mode_colors.get(mode, "white")

            console.print(f"\n[bold magenta]Aleq[/bold magenta] [{mode_color}]({mode})[/{mode_color}]:")
            console.print(Panel(Markdown(response), border_style="dim"))
            console.print()

            # Handle approval if needed
            if mode == "action_proposal":
                approval = console.input("[bold]Approve action? (y/n):[/bold] ")
                if approval.lower() in ["y", "yes"]:
                    state["approval_status"] = "approved"
                    console.print("[green]Approved![/green] Executing...\n")
                    with console.status("[bold green]Executing...[/bold green]"):
                        state = await invoke_cognitive_loop(state, graph, config)
                    response = state.get("final_response", "")
                    console.print(Panel(Markdown(response), border_style="green"))
                else:
                    state["approval_status"] = "rejected"
                    console.print("[yellow]Rejected.[/yellow]\n")

        except KeyboardInterrupt:
            console.print("\n\n[dim]Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")


# ============================================================
# BIRTH COMMAND
# ============================================================

@app.command()
def birth(
    name: str = typer.Argument(..., help="Person's name"),
    email: str = typer.Option(None, "--email", "-e", help="Email address"),
    role: str = typer.Option("Controller", "--role", "-r", help="Role"),
    org_name: str = typer.Option("Default Org", "--org", "-o", help="Organization name"),
    industry: str = typer.Option("general", "--industry", "-i", help="Industry"),
    org_size: str = typer.Option("mid_market", "--size", "-s", help="Org size"),
):
    """Birth a new person into Baby MARS."""
    from .birth.birth_system import birth_person
    from .graphs.belief_graph import reset_belief_graph
    import uuid

    console.print(Panel.fit(f"[bold]Birthing:[/bold] {name}"))

    reset_belief_graph()

    person_id = f"person_{uuid.uuid4().hex[:12]}"
    org_id = f"org_{uuid.uuid4().hex[:12]}"
    email = email or f"{name.lower().replace(' ', '.')}@example.com"

    result = birth_person(
        person_id=person_id,
        name=name,
        email=email,
        role=role,
        org_id=org_id,
        org_name=org_name,
        industry=industry,
        org_size=org_size,
    )

    # Display results
    table = Table(title="Birth Result")
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Person ID", person_id)
    table.add_row("Org ID", org_id)
    table.add_row("Birth Mode", result["birth_mode"])
    table.add_row("Salience", f"{result['salience']:.2f}")
    table.add_row("Belief Count", str(result["belief_count"]))
    table.add_row("Immutable Count", str(result["immutable_count"]))
    table.add_row("Goals", str(len(result["goals"])))

    console.print(table)

    # Show beliefs summary
    console.print("\n[bold]Belief Categories:[/bold]")
    from .graphs.belief_graph import get_belief_graph
    graph = get_belief_graph()

    categories = {}
    for b in graph.beliefs.values():
        cat = b.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items()):
        console.print(f"  {cat}: {count}")


# ============================================================
# BELIEFS COMMAND
# ============================================================

@app.command()
def beliefs(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    min_strength: float = typer.Option(0.0, "--min-strength", "-m", help="Minimum strength"),
):
    """View beliefs in the current graph."""
    from .graphs.belief_graph import get_belief_graph

    graph = get_belief_graph()

    if not graph.beliefs:
        console.print("[dim]No beliefs loaded. Run 'baby-mars birth' first.[/dim]")
        raise typer.Exit(0)

    beliefs_list = list(graph.beliefs.values())

    if category:
        beliefs_list = [b for b in beliefs_list if b.get("category") == category]

    if min_strength > 0:
        beliefs_list = [b for b in beliefs_list if b.get("strength", 0) >= min_strength]

    beliefs_list.sort(key=lambda b: b.get("strength", 0), reverse=True)

    table = Table(title=f"Beliefs ({len(beliefs_list)} total)")
    table.add_column("ID", style="dim", max_width=15)
    table.add_column("Statement", max_width=50)
    table.add_column("Category", style="cyan")
    table.add_column("Strength", justify="right")
    table.add_column("Immutable")

    for b in beliefs_list[:20]:
        immutable = "[green]Yes[/green]" if b.get("immutable") else ""
        strength = b.get("strength", 0)
        strength_color = "green" if strength >= 0.7 else "yellow" if strength >= 0.4 else "red"

        table.add_row(
            b.get("belief_id", "")[:15],
            b.get("statement", "")[:50],
            b.get("category", ""),
            f"[{strength_color}]{strength:.2f}[/{strength_color}]",
            immutable
        )

    console.print(table)

    if len(beliefs_list) > 20:
        console.print(f"\n[dim]Showing 20 of {len(beliefs_list)} beliefs[/dim]")


# ============================================================
# VERSION
# ============================================================

@app.command()
def version():
    """Show version information."""
    console.print(Panel.fit(
        "[bold blue]Baby MARS[/bold blue]\n"
        "Version: 0.1.0\n"
        "Cognitive Architecture with a Rented Brain\n\n"
        "[dim]Implementing Aleq's 20 Research Papers[/dim]",
        title="About"
    ))


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    app()
