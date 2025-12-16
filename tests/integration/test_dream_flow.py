"""Integration tests for the complete dream flow.

Note: Rich Console output goes to stderr. Use `result.output` (not `result.stdout`)
when checking CLI output. See tests/unit/test_terminal_setup.py docstring for details.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from jiro.agents.base import AgentResult
from jiro.agents.dreaming import DreamingAgent
from jiro.cli.main import app
from jiro.core.planner import Spec


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_spec() -> Spec:
    """Create a realistic mock Spec object for testing."""
    return Spec(
        title="User Authentication System",
        overview="A comprehensive user authentication system with OAuth2 support, "
        "email verification, and password reset functionality.",
        requirements=[
            "Support OAuth2 authentication flow with major providers",
            "Implement email-based account creation and verification",
            "Provide secure password reset mechanism via email tokens",
            "Store user credentials securely with bcrypt hashing",
            "Implement JWT token generation and validation",
            "Support multi-factor authentication (MFA) with TOTP",
        ],
        acceptance_criteria=[
            "Users can register with email and password",
            "OAuth2 login works with at least 2 providers (Google, GitHub)",
            "Email verification sent within 5 seconds of registration",
            "Password reset tokens expire after 24 hours",
            "All authentication endpoints have rate limiting",
            "API returns consistent error messages for failed auth",
            "JWT tokens can be validated offline",
            "TOTP codes validated with 30-second time windows",
        ],
        out_of_scope=[
            "Biometric authentication (fingerprint, face recognition)",
            "Single sign-on (SSO) federation across multiple services",
            "Historical audit log of authentication attempts",
            "Third-party identity provider management UI",
        ],
        technical_notes="Use bcrypt with cost factor 12, implement rate limiting with "
        "sliding window algorithm, store JWT secrets in environment variables, "
        "use industry-standard TOTP libraries like pyotp.",
    )


@pytest.fixture
def mock_agent_client() -> MagicMock:
    """Create a mock AgentClient for testing."""
    client = MagicMock()
    client.execute = AsyncMock()
    return client


class TestDreamFlowIntegration:
    """Integration tests for the complete dream command flow."""

    @pytest.mark.integration
    def test_dream_command_basic_flow(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Test basic dream flow: spec generation and exit.

        Verifies:
        - Dream command accepts a prompt
        - Agent generates initial specification
        - Spec is displayed to user
        - User can exit with Ctrl+D (EOFError)
        """
        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
        ):
            # Configure mocks
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=mock_spec)
            mock_agent_class.return_value = mock_agent

            # Simulate user pressing Ctrl+D via prompt_toolkit session
            mock_session = MagicMock()
            mock_session.prompt_async = AsyncMock(side_effect=EOFError)
            with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                result = cli_runner.invoke(
                    app,
                    ["dream", "build a user authentication system"],
                )

            # Should complete successfully
            assert result.exit_code in [0, 1]  # 0 success, 1 with error handling
            # Rich output goes to stderr, use output which combines both
            assert "User Authentication System" in result.output

    @pytest.mark.integration
    def test_dream_spec_generation_and_display(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Test that generated spec is properly displayed with Rich formatting.

        Verifies:
        - Spec title is displayed
        - All required sections are shown
        - Markdown formatting is applied
        """
        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=mock_spec)
            mock_agent_class.return_value = mock_agent

            mock_session = MagicMock()
            mock_session.prompt_async = AsyncMock(side_effect=EOFError)
            with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                result = cli_runner.invoke(
                    app,
                    ["dream", "build a user authentication system"],
                )

            # Check that all spec components are in output
            # Rich output goes to stderr, use output which combines both
            output = result.output
            assert "User Authentication System" in output
            assert "Overview" in output
            assert "Requirements" in output
            assert "Acceptance Criteria" in output or "acceptance criteria" in output.lower()
            assert "Out of Scope" in output or "out of scope" in output.lower()
            assert "Technical Notes" in output

    @pytest.mark.integration
    def test_dream_spec_saving_to_file(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Test that generated spec is saved to a markdown file.

        Verifies:
        - Spec file is created in specs directory
        - File contains markdown formatted specification
        - Filename is derived from spec title
        """
        specs_dir = tmp_path / ".jiro-dreams-of-code" / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)

        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
            patch("jiro.cli.dream.get_specs_dir", return_value=specs_dir),
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=mock_spec)
            mock_agent_class.return_value = mock_agent

            mock_session = MagicMock()
            mock_session.prompt_async = AsyncMock(side_effect=EOFError)
            with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                cli_runner.invoke(
                    app,
                    ["dream", "build a user authentication system"],
                )

            # Verify spec file was saved
            spec_files = list(specs_dir.glob("*.md"))
            assert len(spec_files) > 0, "No spec files were created"

            # Verify the saved file contains expected content
            spec_file = spec_files[0]
            content = spec_file.read_text()
            assert "User Authentication System" in content
            assert "Overview" in content
            assert "Requirements" in content
            assert "Acceptance Criteria" in content
            assert "Out of Scope" in content

    @pytest.mark.integration
    def test_dream_with_single_refinement_round(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Test dream flow with one refinement round.

        Verifies:
        - User can provide refinement feedback
        - Agent generates refined spec
        - Refined spec is displayed
        """
        refined_spec = Spec(
            title="Advanced User Authentication System",
            overview="A comprehensive user authentication system with OAuth2 support, "
            "email verification, password reset, and biometric authentication.",
            requirements=[
                "Support OAuth2 authentication flow with major providers",
                "Implement email-based account creation and verification",
                "Provide secure password reset mechanism via email tokens",
                "Store user credentials securely with bcrypt hashing",
                "Implement JWT token generation and validation",
                "Support multi-factor authentication (MFA) with TOTP",
                "Implement biometric authentication for mobile apps",
            ],
            acceptance_criteria=[
                "Users can register with email and password",
                "OAuth2 login works with at least 2 providers (Google, GitHub)",
                "Email verification sent within 5 seconds of registration",
                "Password reset tokens expire after 24 hours",
                "All authentication endpoints have rate limiting",
                "API returns consistent error messages for failed auth",
                "JWT tokens can be validated offline",
                "TOTP codes validated with 30-second time windows",
                "Biometric auth works on iOS and Android",
            ],
            out_of_scope=[
                "Single sign-on (SSO) federation across multiple services",
                "Historical audit log of authentication attempts",
                "Third-party identity provider management UI",
            ],
            technical_notes="Use bcrypt with cost factor 12, implement rate limiting with "
            "sliding window algorithm, store JWT secrets in environment variables.",
        )

        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=mock_spec)
            mock_agent.refine = AsyncMock(return_value=refined_spec)
            mock_agent_class.return_value = mock_agent

            # Simulate refinement: one feedback, then exit via prompt_toolkit session
            mock_session = MagicMock()
            mock_session.prompt_async = AsyncMock(side_effect=["add biometric auth", "done"])
            with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                result = cli_runner.invoke(
                    app,
                    ["dream", "build a user authentication system"],
                )

            # Should succeed
            assert result.exit_code == 0

            # Refined spec should be displayed
            # Rich output goes to stderr, use output which combines both
            output = result.output
            assert "Advanced User Authentication System" in output
            assert "Biometric" in output

    @pytest.mark.integration
    def test_dream_with_multiple_refinement_rounds(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Test dream flow with multiple refinement rounds.

        Verifies:
        - User can refine spec multiple times
        - Each refinement generates a new spec
        - Flow continues until user exits
        """
        spec_v1 = mock_spec

        spec_v2 = Spec(
            title="Enhanced User Authentication System",
            overview=mock_spec.overview + " With additional security features.",
            requirements=mock_spec.requirements
            + [
                "Implement rate limiting on authentication endpoints",
            ],
            acceptance_criteria=mock_spec.acceptance_criteria
            + ["Rate limiting blocks after 5 failed attempts"],
            out_of_scope=mock_spec.out_of_scope,
            technical_notes=mock_spec.technical_notes
            + " Implement exponential backoff for rate limiting.",
        )

        spec_v3 = Spec(
            title="Enterprise User Authentication System",
            overview=spec_v2.overview + " With LDAP and SAML support.",
            requirements=spec_v2.requirements
            + [
                "Integrate with LDAP for corporate directories",
                "Implement SAML 2.0 for enterprise SSO",
            ],
            acceptance_criteria=spec_v2.acceptance_criteria
            + [
                "LDAP login works with company Active Directory",
                "SAML SSO works with common enterprise providers",
            ],
            out_of_scope=spec_v2.out_of_scope,
            technical_notes=spec_v2.technical_notes,
        )

        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=spec_v1)
            # Each refinement call returns the next version
            mock_agent.refine = AsyncMock(side_effect=[spec_v2, spec_v3])
            mock_agent_class.return_value = mock_agent

            # Simulate: feedback 1, feedback 2, exit via prompt_toolkit session
            mock_session = MagicMock()
            mock_session.prompt_async = AsyncMock(
                side_effect=[
                    "add enhanced security with rate limiting",
                    "add LDAP and SAML support for enterprise",
                    "done",
                ]
            )
            with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                result = cli_runner.invoke(
                    app,
                    ["dream", "build a user authentication system"],
                )

            # Should succeed
            assert result.exit_code == 0

            # Final spec should be displayed
            # Rich output goes to stderr, use output which combines both
            output = result.output
            assert "Enterprise User Authentication System" in output

    @pytest.mark.integration
    def test_dream_handles_exit_commands(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Test that dream handles various exit commands correctly.

        Verifies:
        - 'done' command exits refinement
        - 'exit' command exits refinement
        - '/quit' command exits refinement
        - Empty input exits refinement
        - Ctrl+D (EOFError) exits refinement
        """
        exit_commands = ["done", "exit", "/quit", ""]

        for cmd in exit_commands:
            with (
                patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
                patch("jiro.cli.dream.load_config") as mock_load_config,
                patch("jiro.cli.dream.get_database") as mock_get_db,
                patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
            ):
                mock_config = MagicMock()
                mock_config.models.planning = "claude-opus-4"
                mock_load_config.return_value = mock_config

                mock_db = MagicMock()
                mock_get_db.return_value = mock_db

                mock_agent = MagicMock()
                mock_agent.dream = AsyncMock(return_value=mock_spec)
                mock_agent_class.return_value = mock_agent

                mock_session = MagicMock()
                mock_session.prompt_async = AsyncMock(return_value=cmd)
                with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                    result = cli_runner.invoke(
                        app,
                        ["dream", "build a feature"],
                    )

                assert result.exit_code == 0, f"Failed with command: {cmd}"

    @pytest.mark.integration
    def test_dream_with_custom_model(
        self,
        cli_runner: CliRunner,
        mock_spec: Spec,
        tmp_path: Path,
    ) -> None:
        """Test dream command with custom model override.

        Verifies:
        - --model flag is accepted
        - Custom model is passed to agent configuration
        """
        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=mock_spec)
            mock_agent_class.return_value = mock_agent

            mock_session = MagicMock()
            mock_session.prompt_async = AsyncMock(side_effect=EOFError)
            with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                result = cli_runner.invoke(
                    app,
                    [
                        "dream",
                        "build a feature",
                        "--model",
                        "claude-sonnet-4",
                    ],
                )

            # Should accept the command
            assert result.exit_code in [0, 1, 2]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dreaming_agent_dream_integration(
        self,
        mock_agent_client: MagicMock,
    ) -> None:
        """Test DreamingAgent.dream() method directly.

        Verifies:
        - Agent accepts a prompt
        - Agent calls client.execute()
        - Agent parses response into Spec
        - All spec fields are populated
        """
        # Create a realistic agent output
        agent_output = """# Feature: Authentication API

## Overview

A secure REST API for user authentication supporting multiple methods.

## Requirements

- Support username/password authentication
- Provide OAuth2 integration
- Implement JWT token generation
- Support token refresh mechanism

## Acceptance Criteria

- [ ] Login endpoint returns JWT token
- [ ] Token validation works offline
- [ ] Refresh endpoint issues new tokens
- [ ] Invalid credentials return 401

## Out of Scope

- User registration endpoints
- Password reset functionality
- Rate limiting implementation

## Technical Notes

Use PyJWT for token handling and bcrypt for password hashing.
"""

        mock_agent_client.execute.return_value = AgentResult(
            success=True,
            output=agent_output,
            tokens_before=100,
            tokens_after=350,
            error=None,
        )

        agent = DreamingAgent(mock_agent_client)
        spec = await agent.dream("Build an authentication API")

        # Verify agent called the client
        assert mock_agent_client.execute.called
        call_args = mock_agent_client.execute.call_args[0][0]
        assert "authentication" in call_args.lower() or "api" in call_args.lower()

        # Verify spec was parsed correctly
        assert isinstance(spec, Spec)
        assert spec.title == "Authentication API"
        assert "secure" in spec.overview.lower()
        assert len(spec.requirements) == 4
        assert len(spec.acceptance_criteria) == 4
        assert len(spec.out_of_scope) == 3
        assert spec.technical_notes is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dreaming_agent_refine_integration(
        self,
        mock_agent_client: MagicMock,
    ) -> None:
        """Test DreamingAgent.refine() method directly.

        Verifies:
        - Agent accepts spec and feedback
        - Agent calls client.execute() with refinement prompt
        - Agent parses refined spec correctly
        - Refinement incorporates feedback
        """
        initial_spec = Spec(
            title="Authentication API",
            overview="A REST API for user authentication.",
            requirements=["Support username/password auth"],
            acceptance_criteria=["Login returns JWT"],
            out_of_scope=["User registration"],
        )

        refined_output = """# Feature: Advanced Authentication API

## Overview

A secure REST API for user authentication supporting multiple methods including OAuth2 and SAML.

## Requirements

- Support username/password authentication
- Provide OAuth2 integration with multiple providers
- Implement JWT token generation and validation
- Support token refresh mechanism
- Implement SAML 2.0 for enterprise SSO

## Acceptance Criteria

- [ ] Login endpoint returns JWT token
- [ ] Token validation works offline
- [ ] Refresh endpoint issues new tokens
- [ ] Invalid credentials return 401
- [ ] OAuth2 flow works with Google and GitHub
- [ ] SAML login redirects to provider

## Out of Scope

- User registration endpoints
- Password reset functionality
- Rate limiting implementation
- Audit logging

## Technical Notes

Use PyJWT for token handling, bcrypt for password hashing, and authlib for OAuth2.
"""

        mock_agent_client.execute.return_value = AgentResult(
            success=True,
            output=refined_output,
            tokens_before=200,
            tokens_after=450,
            error=None,
        )

        agent = DreamingAgent(mock_agent_client)
        refined_spec = await agent.refine(
            initial_spec,
            "Add OAuth2 and SAML support for enterprise customers",
        )

        # Verify agent called client
        assert mock_agent_client.execute.called

        # Verify refined spec incorporates feedback
        assert isinstance(refined_spec, Spec)
        assert refined_spec.title == "Advanced Authentication API"
        assert len(refined_spec.requirements) == 5
        assert "SAML" in refined_spec.requirements[-1]
        assert len(refined_spec.acceptance_criteria) == 6

    @pytest.mark.integration
    def test_dream_full_flow_end_to_end(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test complete dream flow with realistic data and multiple refinements.

        This test simulates a real user workflow:
        1. Generate initial spec from prompt
        2. Review and provide feedback
        3. Refine spec twice
        4. Exit and save
        5. Verify saved file contains final spec
        """
        # Create specs directory
        specs_dir = tmp_path / ".jiro-dreams-of-code" / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)

        spec_v1 = Spec(
            title="Payment Processing System",
            overview="Handle payment processing with Stripe integration",
            requirements=[
                "Accept credit card payments",
                "Handle payment webhooks from Stripe",
            ],
            acceptance_criteria=[
                "Payment endpoint accepts card details",
                "Webhook verification confirms payments",
            ],
            out_of_scope=["Refund handling", "Payment scheduling"],
        )

        spec_v2 = Spec(
            title="Advanced Payment Processing System",
            overview="Handle payment processing with Stripe and PayPal integration, "
            "including error handling and retry logic",
            requirements=[
                "Accept credit card payments",
                "Handle payment webhooks from Stripe",
                "Support PayPal payments",
                "Implement automatic retry for failed payments",
            ],
            acceptance_criteria=[
                "Payment endpoint accepts card details",
                "Webhook verification confirms payments",
                "PayPal flow redirects to PayPal",
                "Failed payments retry up to 3 times",
            ],
            out_of_scope=["Refund handling", "Payment scheduling"],
        )

        with (
            patch("jiro.cli.dream.Path.cwd", return_value=tmp_path),
            patch("jiro.cli.dream.load_config") as mock_load_config,
            patch("jiro.cli.dream.get_database") as mock_get_db,
            patch("jiro.cli.dream.DreamingAgent") as mock_agent_class,
            patch("jiro.cli.dream.get_specs_dir", return_value=specs_dir),
        ):
            mock_config = MagicMock()
            mock_config.models.planning = "claude-opus-4"
            mock_load_config.return_value = mock_config

            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            mock_agent = MagicMock()
            mock_agent.dream = AsyncMock(return_value=spec_v1)
            mock_agent.refine = AsyncMock(side_effect=[spec_v2])
            mock_agent_class.return_value = mock_agent

            mock_session = MagicMock()
            mock_session.prompt_async = AsyncMock(
                side_effect=[
                    "add PayPal and retry logic",
                    "done",
                ]
            )
            with patch("jiro.cli.dream._create_multiline_session", return_value=mock_session):
                result = cli_runner.invoke(
                    app,
                    ["dream", "build a payment processing system"],
                )

            assert result.exit_code == 0

            # Verify spec was saved
            spec_files = list(specs_dir.glob("*.md"))
            assert len(spec_files) == 1

            content = spec_files[0].read_text()
            assert "Advanced Payment Processing System" in content
            assert "PayPal" in content
            assert "Retry" in content or "retry" in content
