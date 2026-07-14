import typer

from teselado import __version__

app = typer.Typer(
    name="teselado",
    help="Geospatial zone tessellation and last-mile delivery simulation.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Show package version."""
    typer.echo(f"teselado {__version__}")


@app.command()
def run() -> None:
    """Run the full pipeline (implemented in Phase 2)."""
    typer.echo("Pipeline not yet implemented. See REFACTOR_PLAN.md Phase 2.")
    raise typer.Exit(code=1)
