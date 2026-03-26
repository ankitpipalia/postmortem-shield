from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import yaml

from postmortem_shield.models.incident import Finding, Incident, TimelineEvent

SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
FINDING_PATTERN = re.compile(r"^-\s*\[(F\d{3})\]\s*(.+)$")
FINDING_META_PATTERN = re.compile(r"^\s*-\s*(Evidence|Component|Signal|Severity)\s*:\s*(.+)$")
TIMELINE_PATTERN = re.compile(r"^-\s*(.*?)\s*\|\s*(.+)$")


def _split_frontmatter(raw_text: str) -> tuple[dict[str, object], str]:
    stripped = raw_text.lstrip()
    if not stripped.startswith("---\n"):
        return {}, raw_text

    parts = stripped.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, raw_text

    frontmatter_raw, body = parts
    frontmatter = yaml.safe_load(frontmatter_raw.replace("---\n", "", 1)) or {}
    if not isinstance(frontmatter, dict):
        frontmatter = {}
    return frontmatter, body


def _parse_sections(body: str) -> dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(body))
    if not matches:
        return {}

    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        section_name = match.group(1).strip().lower()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        sections[section_name] = body[start:end].strip()
    return sections


def _parse_services(raw: str) -> list[str]:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    services: list[str] = []
    for line in lines:
        if line.startswith("- "):
            services.append(line[2:].strip())
            continue
        services.extend([part.strip() for part in line.split(",") if part.strip()])
    return sorted(set(services))


def _parse_root_causes(raw: str) -> list[str]:
    causes = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("- "):
            causes.append(line[2:].strip())
        else:
            causes.append(line)
    return causes


def _parse_findings(raw: str) -> list[Finding]:
    findings: list[Finding] = []
    current: dict[str, str] | None = None

    for line in raw.splitlines():
        stripped = line.rstrip()
        if not stripped:
            continue

        match = FINDING_PATTERN.match(stripped)
        if match:
            if current:
                findings.append(
                    Finding(
                        id=current["id"],
                        title=current["title"],
                        evidence=current.get("evidence", current["title"]),
                        impacted_component=current.get("component", "platform"),
                        signal=current.get("signal", "availability"),
                        severity=current.get("severity", "medium"),
                    )
                )
            current = {
                "id": match.group(1),
                "title": match.group(2).strip(),
            }
            continue

        meta_match = FINDING_META_PATTERN.match(stripped)
        if meta_match and current:
            key = meta_match.group(1).lower()
            value = meta_match.group(2).strip()
            if key == "component":
                current["component"] = value
            else:
                current[key] = value.lower() if key == "severity" else value

    if current:
        findings.append(
            Finding(
                id=current["id"],
                title=current["title"],
                evidence=current.get("evidence", current["title"]),
                impacted_component=current.get("component", "platform"),
                signal=current.get("signal", "availability"),
                severity=current.get("severity", "medium"),
            )
        )

    return findings


def _parse_timeline(raw: str) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = TIMELINE_PATTERN.match(stripped)
        if match:
            timestamp_text, description = match.groups()
            timestamp = _safe_datetime(timestamp_text)
            events.append(TimelineEvent(timestamp=timestamp, description=description.strip()))
        elif stripped.startswith("- "):
            events.append(TimelineEvent(description=stripped[2:].strip()))
    return events


def _safe_datetime(value: str | datetime | None) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    candidate = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        return None


def _fallback_incident_id(title: str, source_file: str) -> str:
    base = Path(source_file).stem.lower().replace("_", "-")
    if base:
        return base
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def extract_incident(raw_text: str, source_file: str = "inline") -> Incident:
    frontmatter, body = _split_frontmatter(raw_text)
    sections = _parse_sections(body)

    findings = _parse_findings(sections.get("findings", ""))
    if not findings:
        raise ValueError(
            "No findings parsed; provide at least one [F###] finding in the Findings section"
        )

    title = frontmatter.get("title") or frontmatter.get("incident_title") or "Untitled incident"
    incident_id = frontmatter.get("incident_id") or _fallback_incident_id(title, source_file)
    timeline = _parse_timeline(sections.get("timeline", ""))
    occurred_at = _safe_datetime(frontmatter.get("occurred_at")) or (
        timeline[0].timestamp if timeline and timeline[0].timestamp else None
    )

    return Incident(
        incident_id=incident_id,
        title=title,
        source_file=source_file,
        occurred_at=occurred_at,
        summary=sections.get("summary", "No summary provided"),
        impact=sections.get("impact", "No impact section provided"),
        services=_parse_services(sections.get("services", "")),
        root_causes=_parse_root_causes(sections.get("root causes", "")),
        findings=findings,
        timeline=timeline,
    )
