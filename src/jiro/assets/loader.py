"""Asset loading system with resolution order: local -> project -> global -> package."""

from pathlib import Path


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


def list_assets() -> dict[str, Path]:
    """
    List all available assets and their source locations.

    Returns:
        Dictionary mapping asset paths to their source locations
    """
    # TODO: Implement asset listing
    raise NotImplementedError("Asset listing not yet implemented")
