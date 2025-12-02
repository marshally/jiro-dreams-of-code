"""Spec parser and planner for feature specifications."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from jiro.agents.client import AgentClient
from jiro.trackers.interface import IssueTracker
from jiro.trackers.interface import Task as TrackerTask


@dataclass
class Spec:
    """A parsed feature specification."""

    title: str
    overview: str
    requirements: list[str]
    acceptance_criteria: list[str]
    out_of_scope: list[str]
    technical_notes: str | None = None


@dataclass
class Epic:
    """An epic representing a parallel workstream."""

    id: str
    name: str
    description: str
    tasks: list[str] = field(default_factory=list)


@dataclass
class Task:
    """A task within an epic."""

    id: str
    title: str
    description: str
    epic_id: str
    dependencies: list[str] = field(default_factory=list)


@dataclass
class PlanResult:
    """Result of planning a spec into epics and tasks."""

    epics: list[Epic] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    dependencies: list[dict] = field(default_factory=list)


class SpecPlanner:
    """Plans a spec into epics, tasks, and dependencies using LLM decomposition."""

    def __init__(self, client: AgentClient) -> None:
        """Initialize SpecPlanner.

        Args:
            client: AgentClient for LLM-based decomposition.

        Raises:
            TypeError: If client is None.
        """
        if client is None:
            raise TypeError("client cannot be None")
        self.client = client

    async def plan(self, spec: Spec) -> PlanResult:
        """Plan a spec into epics and tasks.

        Args:
            spec: The specification to plan.

        Returns:
            PlanResult containing generated epics, tasks, and dependencies.
        """
        # Create the planning prompt
        prompt = self._create_planning_prompt(spec)

        # Execute the agent to get decomposition
        result = await self.client.execute(prompt)

        # Parse the response
        return self._parse_plan_result(result.output, spec)

    def _create_planning_prompt(self, spec: Spec) -> str:
        """Create the prompt for spec planning.

        Args:
            spec: The specification to plan.

        Returns:
            A prompt string for the LLM.
        """
        requirements_str = "\n".join(f"  - {r}" for r in spec.requirements)
        criteria_str = "\n".join(f"  - {c}" for c in spec.acceptance_criteria)
        out_of_scope_str = "\n".join(f"  - {o}" for o in spec.out_of_scope)

        prompt = f"""You are a task decomposition expert. Break down the following feature specification into parallel epics and detailed tasks.

Feature: {spec.title}

Overview:
{spec.overview}

Requirements:
{requirements_str}

Acceptance Criteria:
{criteria_str}

Out of Scope:
{out_of_scope_str}

{f"Technical Notes:{chr(10)}{spec.technical_notes}" if spec.technical_notes else ""}

Generate a JSON response with this exact structure:
{{
  "epics": [
    {{
      "id": "epic-1",
      "name": "Epic Name",
      "description": "Epic description",
      "tasks": ["task-1", "task-2"]
    }}
  ],
  "tasks": [
    {{
      "id": "task-1",
      "title": "Task Title",
      "description": "Task description",
      "epic_id": "epic-1",
      "dependencies": ["task-0"]
    }}
  ],
  "dependencies": [
    {{"from": "task-1", "to": "task-0"}}
  ]
}}

Requirements:
1. Create 2-4 parallel epics representing different workstreams
2. Each epic should have 2-4 tasks
3. Analyze task dependencies intelligently
4. Tasks in the same epic can often run in parallel
5. Cross-epic dependencies should be minimized
6. Return ONLY valid JSON, no markdown or extra text"""
        return prompt

    def _parse_plan_result(self, response: str, spec: Spec) -> PlanResult:
        """Parse the LLM response into a PlanResult.

        Args:
            response: The raw response from the LLM.
            spec: The original spec (for context).

        Returns:
            A PlanResult object.
        """
        # Handle empty response
        if not response or not response.strip():
            return PlanResult()

        try:
            # Extract JSON from response (in case there's extra text)
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            # Parse epics
            epics = []
            if "epics" in data:
                for epic_data in data["epics"]:
                    epic = Epic(
                        id=epic_data.get("id", f"epic-{len(epics)}"),
                        name=epic_data.get("name", ""),
                        description=epic_data.get("description", ""),
                        tasks=epic_data.get("tasks", []),
                    )
                    epics.append(epic)

            # Parse tasks
            tasks = []
            if "tasks" in data:
                for task_data in data["tasks"]:
                    task = Task(
                        id=task_data.get("id", f"task-{len(tasks)}"),
                        title=task_data.get("title", ""),
                        description=task_data.get("description", ""),
                        epic_id=task_data.get("epic_id", ""),
                        dependencies=task_data.get("dependencies", []),
                    )
                    tasks.append(task)

            # Parse dependencies
            dependencies = data.get("dependencies", [])

            return PlanResult(epics=epics, tasks=tasks, dependencies=dependencies)

        except json.JSONDecodeError:
            # Return empty result if JSON parsing fails
            return PlanResult()

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that may contain markdown or extra text.

        Args:
            text: The text to extract JSON from.

        Returns:
            The extracted JSON string.
        """
        # Try to find JSON block
        start_idx = text.find("{")
        if start_idx == -1:
            return "{}"

        # Find matching closing brace
        brace_count = 0
        for i in range(start_idx, len(text)):
            if text[i] == "{":
                brace_count += 1
            elif text[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start_idx : i + 1]

        return text[start_idx:]


def parse_spec(path: Path) -> Spec:
    """
    Parse a feature specification markdown file.

    Args:
        path: Path to the specification markdown file.

    Returns:
        Spec dataclass with parsed sections.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If required sections are missing.
    """
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {path}")

    content = path.read_text()

    # Extract title from # Feature: Title
    title = _extract_title(content)
    if not title:
        raise ValueError("Title (# Feature: ...) section is required")

    # Extract sections
    overview = _extract_section(content, "Overview")
    if not overview:
        raise ValueError("Overview section is required")

    requirements = _extract_list_section(content, "Requirements")
    if not requirements:
        raise ValueError("Requirements section is required")

    acceptance_criteria = _extract_list_section(content, "Acceptance Criteria")
    if not acceptance_criteria:
        raise ValueError("Acceptance Criteria section is required")

    out_of_scope = _extract_list_section(content, "Out of Scope")
    if not out_of_scope:
        raise ValueError("Out of Scope section is required")

    technical_notes = _extract_section(content, "Technical Notes")

    return Spec(
        title=title,
        overview=overview,
        requirements=requirements,
        acceptance_criteria=acceptance_criteria,
        out_of_scope=out_of_scope,
        technical_notes=technical_notes,
    )


def _extract_title(content: str) -> str | None:
    """Extract title from # Feature: Title format."""
    match = re.search(r"^#\s+Feature:\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def _extract_section(content: str, section_name: str) -> str | None:
    """Extract text content of a section by heading."""
    # Match ## Section Name and capture everything until next ## or EOF
    pattern = rf"^##\s+{re.escape(section_name)}$\n(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        text = match.group(1).strip()
        # Remove list markers if they exist
        lines = text.split("\n")
        # Filter out list items and join remaining paragraphs
        non_list_lines = []
        for line in lines:
            if not line.strip().startswith("-") and not line.strip().startswith("["):
                non_list_lines.append(line)
        result = "\n".join(non_list_lines).strip()
        return result if result else None
    return None


def _extract_list_section(content: str, section_name: str) -> list[str]:
    """Extract list items from a section."""
    # Match ## Section Name and capture everything until next ## or EOF
    pattern = rf"^##\s+{re.escape(section_name)}$\n(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return []

    section_text = match.group(1)
    items = []

    # Split by lines and look for list items starting with - or [ ]
    lines = section_text.split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("-"):
            # Remove leading dash and whitespace
            item = stripped[1:].strip()
            items.append(item)

    return items


def create_tasks(plan: PlanResult, tracker: IssueTracker) -> list[TrackerTask]:
    """Create tasks from a plan in the issue tracker.

    Creates epics first, then creates tasks linked to those epics with dependencies.

    Args:
        plan: The PlanResult containing epics, tasks, and dependencies.
        tracker: The IssueTracker implementation to use.

    Returns:
        List of created TrackerTask objects.
    """
    created_tasks: list[TrackerTask] = []
    # Map from plan IDs to created tracker IDs
    plan_id_to_tracker_id: dict[str, str] = {}

    # Create all epics first
    for epic in plan.epics:
        created_epic = tracker.create_task(
            title=epic.name,
            description=epic.description,
            task_type="epic",
        )
        plan_id_to_tracker_id[epic.id] = created_epic.id
        created_tasks.append(created_epic)

    # Create all tasks, linking to their parent epics
    for task in plan.tasks:
        # Get the tracker ID for the parent epic
        epic_tracker_id = plan_id_to_tracker_id.get(task.epic_id)

        created_task = tracker.create_task(
            title=task.title,
            description=task.description,
            task_type="task",
            epic_id=epic_tracker_id,
        )
        plan_id_to_tracker_id[task.id] = created_task.id
        created_tasks.append(created_task)

    # Set up dependencies between tasks
    for dep in plan.dependencies:
        from_id = dep.get("from")
        to_id = dep.get("to")

        if from_id and to_id:
            # Convert plan IDs to tracker IDs
            from_tracker_id = plan_id_to_tracker_id.get(from_id)
            to_tracker_id = plan_id_to_tracker_id.get(to_id)

            if from_tracker_id and to_tracker_id:
                tracker.add_dependency(from_tracker_id, to_tracker_id)

    return created_tasks
