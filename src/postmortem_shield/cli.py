from __future__ import annotations

import json
from pathlib import Path

import typer
import uvicorn

from postmortem_shield.config import DEFAULT_OUTPUT_DIR, DEFAULT_SAMPLE_POSTMORTEM
from postmortem_shield.pipeline import ShieldPipeline

app = typer.Typer(add_completion=False, help="Generate prevention artifacts from postmortems.")


def _print_summary(bundle: dict) -> None:
    typer.echo(f"Incident: {bundle['incident']['incident_id']} :: {bundle['incident']['title']}")
    for artifact in bundle["artifacts"]:
        validation = artifact.get("validation") or {}
        status = "PASS" if validation.get("ok") else "FAIL"
        validator = validation.get("validator", "n/a")
        typer.echo(
            f"  - {artifact['artifact_type']}: "
            f"{artifact['filename']} [{status}] via {validator}"
        )


@app.command("generate")
def generate_command(
    input_file: Path = typer.Option(..., "--input", exists=True, dir_okay=False, readable=True),
    output_dir: Path = typer.Option(DEFAULT_OUTPUT_DIR, "--output"),
    provider: str = typer.Option("mock", "--provider", help="Generation provider (default: mock)."),
    fail_on_validation: bool = typer.Option(False, "--fail-on-validation"),
) -> None:
    pipeline = ShieldPipeline(provider_name=provider)
    bundle = pipeline.run(input_file, output_dir)
    serialized = bundle.model_dump(mode="json")
    _print_summary(serialized)

    if fail_on_validation and not all(a["validation"]["ok"] for a in serialized["artifacts"]):
        raise typer.Exit(code=2)


@app.command("demo")
def demo_command(
    input_file: Path = typer.Option(
        DEFAULT_SAMPLE_POSTMORTEM,
        "--input",
        exists=True,
        dir_okay=False,
    ),
    output_dir: Path = typer.Option(DEFAULT_OUTPUT_DIR, "--output"),
) -> None:
    pipeline = ShieldPipeline(provider_name="mock")
    bundle = pipeline.run(input_file, output_dir)
    serialized = bundle.model_dump(mode="json")
    _print_summary(serialized)
    typer.echo(json.dumps(bundle.traceability, indent=2))


@app.command("serve")
def serve_command(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8000, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    uvicorn.run("postmortem_shield.api.main:app", host=host, port=port, reload=reload)


def main() -> None:
    app()
