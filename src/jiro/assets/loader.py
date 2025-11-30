"""Asset loading system with resolution order: local -> project -> global -> package."""

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template


@dataclass
class AssetInfo:
    """Information about an available asset."""

    name: str
    asset_type: str  # "prompt" or "template"
    path: Path


def load_prompt(name: str) -> str:
    """
    Load a prompt from the package assets.

    Args:
        name: Name of the prompt file (e.g., "planning_agent.md")

    Returns:
        Prompt content as string

    Raises:
        FileNotFoundError: If prompt not found
    """
    asset_path = get_asset_path(name)
    return asset_path.read_text()


def load_template(name: str) -> Template:
    """
    Load a Jinja2 template from the package assets.

    Args:
        name: Name of the template file relative to templates dir
              (e.g., "commit/docs.txt.j2")

    Returns:
        Jinja2 Template object

    Raises:
        FileNotFoundError: If template not found
    """
    asset_path = get_asset_path(name)
    # Load the template using Jinja2 Environment
    env = Environment(loader=FileSystemLoader(str(asset_path.parent)))
    return env.get_template(asset_path.name)


def list_assets() -> list[AssetInfo]:
    """
    List all available assets.

    Returns:
        List of AssetInfo objects describing available assets
    """
    assets: list[AssetInfo] = []
    assets_dir = _get_package_assets_dir()

    # Scan prompts directory
    prompts_dir = assets_dir / "prompts"
    if prompts_dir.exists():
        for prompt_file in prompts_dir.glob("*.md"):
            if prompt_file.is_file():
                assets.append(
                    AssetInfo(
                        name=prompt_file.name,
                        asset_type="prompt",
                        path=prompt_file,
                    )
                )

    # Scan templates directory
    templates_dir = assets_dir / "templates"
    if templates_dir.exists():
        for template_file in templates_dir.rglob("*.j2"):
            if template_file.is_file():
                # Store relative path from templates root
                rel_path = template_file.relative_to(templates_dir)
                assets.append(
                    AssetInfo(
                        name=str(rel_path),
                        asset_type="template",
                        path=template_file,
                    )
                )

    return assets


def get_asset_path(name: str) -> Path:
    """
    Get the path to an asset by name.

    Searches in prompts and templates directories.

    Args:
        name: Name of the asset (e.g., "planning_agent.md" or "commit/docs.txt.j2")

    Returns:
        Absolute path to the asset

    Raises:
        FileNotFoundError: If asset not found
    """
    assets_dir = _get_package_assets_dir()

    # Try prompts directory
    prompt_path = assets_dir / "prompts" / name
    if prompt_path.exists():
        return prompt_path

    # Try templates directory
    template_path = assets_dir / "templates" / name
    if template_path.exists():
        return template_path

    raise FileNotFoundError(f"Asset not found: {name}")


def _get_package_assets_dir() -> Path:
    """Get the package assets directory path."""
    return Path(__file__).parent


def load_asset(asset_path: str) -> str:
    """
    Load an asset with resolution order.

    Resolution order (highest to lowest):
    1. Local (.jiro-dreams-of-code/assets/)
    2. Project (~/.jiro-dreams-of-code/$PROJECT_NAME/assets/)
    3. Global (~/.jiro-dreams-of-code/assets/)
    4. Package defaults (bundled in jiro package)

    Args:
        asset_path: Relative path to asset (e.g., "prompts/dreaming_agent.md")

    Returns:
        Asset content as string

    Raises:
        FileNotFoundError: If asset not found in any location
    """
    # TODO: Implement asset resolution logic
    raise NotImplementedError("Asset loading not yet implemented")


def which_asset(asset_path: str) -> Path:
    """
    Show which location an asset will be loaded from.

    Args:
        asset_path: Relative path to asset

    Returns:
        Absolute path to the asset that would be loaded

    Raises:
        FileNotFoundError: If asset not found in any location
    """
    # TODO: Implement asset resolution logic
    raise NotImplementedError("Asset which not yet implemented")
