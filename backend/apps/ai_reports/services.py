"""Match report generation isolated behind a provider boundary."""

from dataclasses import dataclass
import json
import os
from typing import Protocol
from urllib import error, request

from apps.matches.models import Match


@dataclass(frozen=True)
class MatchSummary:
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    goals: tuple[str, ...]

    def as_dict(self) -> dict:
        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "goals": list(self.goals),
        }


@dataclass(frozen=True)
class GeneratedReport:
    text: str


class MatchReportGenerator(Protocol):
    def generate(self, summary: MatchSummary) -> GeneratedReport:
        """Generate a short plain-text report from the minimal match summary."""


class TemplateMatchReportGenerator:
    """Safe local provider used when no external LLM is configured."""

    def generate(self, summary: MatchSummary) -> GeneratedReport:
        if summary.home_score == summary.away_score:
            result = f"{summary.home_team} and {summary.away_team} drew {summary.home_score}-{summary.away_score}."
        else:
            winner = summary.home_team if summary.home_score > summary.away_score else summary.away_team
            result = f"{winner} secured a {summary.home_score}-{summary.away_score} victory over {summary.away_team if winner == summary.home_team else summary.home_team}."
        if summary.goals:
            result += " Goals: " + "; ".join(summary.goals) + "."
        return GeneratedReport(text=result)


class OpenAIResponsesGenerator:
    """Optional OpenAI Responses API adapter; raw output is validated upstream."""

    endpoint = "https://api.openai.com/v1/responses"

    def generate(self, summary: MatchSummary) -> GeneratedReport:
        api_key = os.environ["OPENAI_API_KEY"]
        payload = {
            "model": os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            "input": [
                {
                    "role": "system",
                    "content": "Write one concise, factual football match report in English.",
                },
                {"role": "user", "content": json.dumps(summary.as_dict())},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "match_report",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {"report": {"type": "string"}},
                        "required": ["report"],
                        "additionalProperties": False,
                    },
                }
            },
        }
        body = json.dumps(payload).encode()
        req = request.Request(
            self.endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read())
        except (error.URLError, TimeoutError) as exc:
            raise ConnectionError("AI provider request failed") from exc
        output_text = data.get("output_text")
        if not output_text:
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") in {"output_text", "text"}:
                        output_text = content.get("text")
                        break
        if not output_text:
            raise ValueError("AI provider returned no report.")
        parsed = json.loads(output_text)
        if not isinstance(parsed, dict) or not isinstance(parsed.get("report"), str):
            raise ValueError("AI provider returned an invalid structured report.")
        return GeneratedReport(text=parsed["report"])


def build_match_summary(match: Match) -> MatchSummary:
    fixture = match.fixture
    goals = tuple(
        f"{event.minute}' {event.player.full_name} ({event.team.name})"
        for event in match.events.all()
        if event.event_type == "GOAL"
    )
    return MatchSummary(
        home_team=fixture.home_team.name,
        away_team=fixture.away_team.name,
        home_score=match.home_score,
        away_score=match.away_score,
        goals=goals,
    )


def validate_generated_report(value: GeneratedReport) -> GeneratedReport:
    text = value.text.strip()
    if not text or len(text) > 2000:
        raise ValueError("The generated report must contain 1-2000 characters.")
    return GeneratedReport(text=text)


def get_match_report_generator() -> MatchReportGenerator:
    if os.getenv("AI_MATCH_REPORT_PROVIDER", "template").lower() == "openai":
        return OpenAIResponsesGenerator()
    # The deterministic provider keeps local deployments offline. An external
    # provider can implement the protocol without changing match lifecycle code.
    return TemplateMatchReportGenerator()
