"""FastAPI web application for jiro-dreams-of-code."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

# Initialize FastAPI app
app = FastAPI(title="jiro-dreams-of-code", version="0.1.0")

# Setup Jinja2 template environment
# Use the package's assets/templates directory
assets_dir = Path(__file__).parent.parent / "assets"
templates_dir = assets_dir / "templates"

# Create Jinja2 environment
template_env = Environment(
    loader=FileSystemLoader(str(templates_dir)),
    autoescape=True,
)


# Mount static files if static directory exists
static_dir = assets_dir / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/health", response_model=dict[str, str])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    """Render the home page template."""
    try:
        template = template_env.get_template("index.html")
        return template.render()
    except Exception:
        # Fallback if template doesn't exist
        return "<html><body><h1>Welcome to jiro-dreams-of-code</h1></body></html>"
