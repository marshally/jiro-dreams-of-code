"""Tests for asset loader system."""

from pathlib import Path

import pytest
from jinja2 import Template

from jiro.assets.loader import AssetInfo


class TestLoadPrompt:
    """Tests for load_prompt function."""

    @pytest.mark.unit
    def test_load_prompt_returns_string(self) -> None:
        """load_prompt should return string content."""
        from jiro.assets.loader import load_prompt

        content = load_prompt("planning_agent.md")
        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.unit
    def test_load_prompt_planning_agent(self) -> None:
        """load_prompt should load planning_agent.md content."""
        from jiro.assets.loader import load_prompt

        content = load_prompt("planning_agent.md")
        assert "planning" in content.lower() or "plan" in content.lower()

    @pytest.mark.unit
    def test_load_prompt_execution_agent(self) -> None:
        """load_prompt should load execution_agent.md content."""
        from jiro.assets.loader import load_prompt

        content = load_prompt("execution_agent.md")
        assert "execution" in content.lower() or "execut" in content.lower()

    @pytest.mark.unit
    def test_load_prompt_review_agent(self) -> None:
        """load_prompt should load review_agent.md content."""
        from jiro.assets.loader import load_prompt

        content = load_prompt("review_agent.md")
        assert "review" in content.lower()

    @pytest.mark.unit
    def test_load_prompt_dreaming_agent(self) -> None:
        """load_prompt should load dreaming_agent.md content."""
        from jiro.assets.loader import load_prompt

        content = load_prompt("dreaming_agent.md")
        assert "dream" in content.lower() or "spec" in content.lower()

    @pytest.mark.unit
    def test_load_prompt_not_found(self) -> None:
        """load_prompt should raise FileNotFoundError for missing prompt."""
        from jiro.assets.loader import load_prompt

        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent_prompt.md")


class TestLoadTemplate:
    """Tests for load_template function."""

    @pytest.mark.unit
    def test_load_template_returns_template(self) -> None:
        """load_template should return a Jinja2 Template object."""
        from jiro.assets.loader import load_template

        template = load_template("commit/docs.txt.j2")
        assert isinstance(template, Template)

    @pytest.mark.unit
    def test_load_template_docs(self) -> None:
        """load_template should load docs.txt.j2."""
        from jiro.assets.loader import load_template

        template = load_template("commit/docs.txt.j2")
        # Template should be renderable
        rendered = template.render(
            task_id="123",
            reason="test",
            task_type="feature",
            verification_command="pytest",
            verification_results="PASSED",
            time_taken_seconds=10,
            context_tokens_before=1000,
            context_tokens_after=1200,
        )
        assert isinstance(rendered, str)
        assert "123" in rendered

    @pytest.mark.unit
    def test_load_template_not_found(self) -> None:
        """load_template should raise FileNotFoundError for missing template."""
        from jiro.assets.loader import load_template

        with pytest.raises(FileNotFoundError):
            load_template("nonexistent/template.j2")


class TestListAssets:
    """Tests for list_assets function."""

    @pytest.mark.unit
    def test_list_assets_returns_list(self) -> None:
        """list_assets should return a list."""
        from jiro.assets.loader import list_assets

        assets = list_assets()
        assert isinstance(assets, list)

    @pytest.mark.unit
    def test_list_assets_contains_asset_info(self) -> None:
        """list_assets should return list of AssetInfo objects."""
        from jiro.assets.loader import list_assets

        assets = list_assets()
        assert len(assets) > 0
        for asset in assets:
            assert isinstance(asset, AssetInfo)
            assert hasattr(asset, "name")
            assert hasattr(asset, "asset_type")
            assert hasattr(asset, "path")

    @pytest.mark.unit
    def test_list_assets_includes_prompts(self) -> None:
        """list_assets should include prompt files."""
        from jiro.assets.loader import list_assets

        assets = list_assets()
        prompt_assets = [a for a in assets if a.asset_type == "prompt"]
        assert len(prompt_assets) > 0
        prompt_names = {a.name for a in prompt_assets}
        assert "planning_agent.md" in prompt_names
        assert "execution_agent.md" in prompt_names
        assert "review_agent.md" in prompt_names
        assert "dreaming_agent.md" in prompt_names

    @pytest.mark.unit
    def test_list_assets_includes_templates(self) -> None:
        """list_assets should include template files."""
        from jiro.assets.loader import list_assets

        assets = list_assets()
        template_assets = [a for a in assets if a.asset_type == "template"]
        assert len(template_assets) > 0
        template_names = {a.name for a in template_assets}
        assert any("docs.txt.j2" in name for name in template_names)

    @pytest.mark.unit
    def test_list_assets_paths_exist(self) -> None:
        """All asset paths returned by list_assets should exist."""
        from jiro.assets.loader import list_assets

        assets = list_assets()
        for asset in assets:
            assert asset.path.exists(), f"Asset path does not exist: {asset.path}"

    @pytest.mark.unit
    def test_list_assets_asset_types_valid(self) -> None:
        """All asset types should be 'prompt' or 'template'."""
        from jiro.assets.loader import list_assets

        assets = list_assets()
        valid_types = {"prompt", "template"}
        for asset in assets:
            assert asset.asset_type in valid_types


class TestGetAssetPath:
    """Tests for get_asset_path function."""

    @pytest.mark.unit
    def test_get_asset_path_returns_path(self) -> None:
        """get_asset_path should return a Path object."""
        from jiro.assets.loader import get_asset_path

        path = get_asset_path("planning_agent.md")
        assert isinstance(path, Path)

    @pytest.mark.unit
    def test_get_asset_path_prompt_exists(self) -> None:
        """get_asset_path should return path that exists for prompts."""
        from jiro.assets.loader import get_asset_path

        path = get_asset_path("planning_agent.md")
        assert path.exists(), f"Asset path does not exist: {path}"

    @pytest.mark.unit
    def test_get_asset_path_template_exists(self) -> None:
        """get_asset_path should return path that exists for templates."""
        from jiro.assets.loader import get_asset_path

        path = get_asset_path("commit/docs.txt.j2")
        assert path.exists(), f"Asset path does not exist: {path}"

    @pytest.mark.unit
    def test_get_asset_path_correct_extension_prompt(self) -> None:
        """get_asset_path should return correct extension for prompts."""
        from jiro.assets.loader import get_asset_path

        path = get_asset_path("planning_agent.md")
        assert path.suffix == ".md"

    @pytest.mark.unit
    def test_get_asset_path_correct_extension_template(self) -> None:
        """get_asset_path should return correct extension for templates."""
        from jiro.assets.loader import get_asset_path

        path = get_asset_path("commit/docs.txt.j2")
        assert path.suffix == ".j2"

    @pytest.mark.unit
    def test_get_asset_path_not_found(self) -> None:
        """get_asset_path should raise FileNotFoundError for missing asset."""
        from jiro.assets.loader import get_asset_path

        with pytest.raises(FileNotFoundError):
            get_asset_path("nonexistent.txt")
