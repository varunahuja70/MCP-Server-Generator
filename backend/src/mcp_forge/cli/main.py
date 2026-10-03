"""MCP Forge Command Line Interface."""

import typer

from mcp_forge.version import __version__

app = typer.Typer(
    name="forge",
    help="MCP Forge - Generate MCP servers from OpenAPI specs.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"mcp-forge version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """MCP Forge CLI root callback."""


@app.command()
def check(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI specification"),
) -> None:
    """Validate an OpenAPI specification."""
    typer.echo(f"Checking spec: {spec}")


@app.command()
def review(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI specification"),
) -> None:
    """Review an OpenAPI specification for security and quality."""
    typer.echo(f"Reviewing spec: {spec}")


@app.command()
def generate(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI specification"),
    output: str = typer.Option("-o", "--output", help="Output directory for generated server"),
) -> None:
    """Generate an MCP server project from an OpenAPI specification."""
    typer.echo(f"Generating from {spec} into {output}")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind Forge web app"),
    port: int = typer.Option(8080, "--port", help="Port to bind Forge web app"),
) -> None:
    """Start the Forge web server and dashboard."""
    typer.echo(f"Starting MCP Forge server on {host}:{port}")


@app.command()
def samples() -> None:
    """List bundled sample specifications."""
    typer.echo("Bundled sample specifications available.")


@app.command()
def wipe() -> None:
    """Wipe all stored data."""
    typer.echo("Wiping all local data.")


if __name__ == "__main__":
    app()
