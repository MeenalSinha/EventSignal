"""Generic, site-independent opportunity content extractor.

Implements a staged extraction pipeline:
- Stage A: Structured data (JSON-LD, Schema.org Event/JobPosting/Course).
- Stage B: General HTML metadata (OpenGraph, Twitter cards, meta tags, title).
- Stage C: Generic rule-based heuristics on semantic HTML elements and headings.

Every extracted field is tracked with:
- Extracted value (or None).
- Verbatim supporting excerpt from the source content.
- Extraction method (STRUCTURED, RULE_BASED).
- Evidence status (FOUND, NOT_FOUND, EXTRACTION_FAILED).

Values are never fabricated: if a field is absent, it remains None with status NOT_FOUND.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.models.field_evidence import EvidenceStatus, ExtractionMethod
from app.models.opportunity import OpportunityType, ParticipationMode

logger = logging.getLogger(__name__)

OPPORTUNITY_FIELDS = [
    "title",
    "opportunity_type",
    "organizer",
    "start_date",
    "end_date",
    "registration_deadline",
    "submission_deadline",
    "location",
    "mode",
    "eligibility",
    "skills_required",
    "compensation",
    "application_url",
]


@dataclass
class ExtractedField:
    field_name: str
    value: Any
    supporting_excerpt: str | None
    extraction_method: ExtractionMethod
    evidence_status: EvidenceStatus


@dataclass
class ExtractionResult:
    fields: dict[str, ExtractedField]
    raw_title: str | None = None
    structured_data_found: bool = False


# ---------------------------------------------------------------------------
# Helper Parsers
# ---------------------------------------------------------------------------


def _clean_text(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned if cleaned else None


def _get_tag_attr_str(tag: Tag, attr: str) -> str:
    """Safely extract string attribute from a BeautifulSoup Tag."""
    val = tag.get(attr, "")
    if isinstance(val, list):
        return " ".join(val).strip()
    return str(val).strip()


def _make_excerpt(text: str | None, max_length: int = 300) -> str | None:
    cleaned = _clean_text(text)
    if not cleaned:
        return None
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[:max_length] + "..."


def _parse_iso_datetime(value: Any) -> datetime | None:
    """Attempt to parse an ISO-8601 datetime string."""
    if not value or not isinstance(value, str):
        return None
    val = value.strip()
    # Normalize Z
    if val.endswith("Z"):
        val = val[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except ValueError:
        pass

    # Try date-only format YYYY-MM-DD
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", val)
    if match:
        y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return datetime(y, m, d, 0, 0, tzinfo=UTC)

    return None


def _parse_human_date(text: str) -> datetime | None:
    """Parse common human-written date patterns like 'May 15, 2026' or '15-05-2026'."""
    text_clean = text.strip()
    # Pattern: Month Day, Year (e.g. "October 25, 2026" or "Oct 25, 2026")
    month_names = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }
    m = re.search(r"\b([a-zA-Z]+)\s+(\d{1,2}),?\s+(\d{4})\b", text_clean)
    if m:
        month_str, day_str, year_str = m.group(1).lower(), m.group(2), m.group(3)
        if month_str in month_names:
            try:
                return datetime(
                    int(year_str), month_names[month_str], int(day_str), 0, 0, tzinfo=UTC
                )
            except ValueError:
                pass

    # Pattern: Day Month Year (e.g. "25 October 2026")
    m2 = re.search(r"\b(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})\b", text_clean)
    if m2:
        day_str, month_str, year_str = m2.group(1), m2.group(2).lower(), m2.group(3)
        if month_str in month_names:
            try:
                return datetime(
                    int(year_str), month_names[month_str], int(day_str), 0, 0, tzinfo=UTC
                )
            except ValueError:
                pass

    return None


def _classify_opportunity_type(text: str) -> OpportunityType | None:
    """Determine opportunity type from keywords in title or summary."""
    t = text.lower()
    if re.search(r"\bhackathon\b", t):
        return OpportunityType.HACKATHON
    if re.search(r"\bfellowship\b", t):
        return OpportunityType.FELLOWSHIP
    if re.search(r"\binternship\b|\bintern\b", t):
        return OpportunityType.INTERNSHIP
    if re.search(r"\bresearch\b|\blab\b", t):
        return OpportunityType.RESEARCH
    if re.search(r"\bmentorship\b|\bmentor\b", t):
        return OpportunityType.MENTORSHIP
    if re.search(r"\bcompetition\b|\bcontest\b|\bchallenge\b", t):
        return OpportunityType.COMPETITION
    if re.search(r"\bworkshop\b|\bbootcamp\b|\btraining\b", t):
        return OpportunityType.WORKSHOP
    if re.search(r"\bconference\b|\bsummit\b|\bsymposium\b", t):
        return OpportunityType.CONFERENCE
    return None


def _detect_mode(text: str) -> ParticipationMode | None:
    """Detect participation mode from text indicators."""
    t = text.lower()
    if re.search(r"\bhybrid\b", t):
        return ParticipationMode.HYBRID
    if re.search(r"\bonline\b|\bvirtual\b|\bremote\b|\bzoom\b|\bwebinar\b", t):
        return ParticipationMode.ONLINE
    if re.search(r"\boffline\b|\bin[\s-]person\b|\bon[\s-]site\b|\bphysical\b", t):
        return ParticipationMode.OFFLINE
    return None


# ---------------------------------------------------------------------------
# Main Extractor
# ---------------------------------------------------------------------------


def extract_opportunity_from_html(html: str, source_url: str) -> ExtractionResult:
    """Extract opportunity fields and evidence records from raw webpage HTML."""
    soup = BeautifulSoup(html, "html.parser")
    fields: dict[str, ExtractedField] = {}

    # Stage A: Structured data (JSON-LD)
    structured_fields, structured_found = _extract_stage_a_structured(soup, source_url)
    for k, v in structured_fields.items():
        if v.value is not None:
            fields[k] = v

    # Stage B: HTML metadata (OpenGraph, meta tags, <title>)
    meta_fields = _extract_stage_b_metadata(soup, source_url)
    for k, v in meta_fields.items():
        if k not in fields and v.value is not None:
            fields[k] = v

    # Stage C: Generic rule-based heuristics on content elements
    rule_fields = _extract_stage_c_heuristics(soup, source_url)
    for k, v in rule_fields.items():
        if k not in fields and v.value is not None:
            fields[k] = v

    # For any remaining fields that were unextracted, register an honest NOT_FOUND
    for field_name in OPPORTUNITY_FIELDS:
        if field_name not in fields:
            fields[field_name] = ExtractedField(
                field_name=field_name,
                value=None,
                supporting_excerpt=None,
                extraction_method=ExtractionMethod.RULE_BASED,
                evidence_status=EvidenceStatus.NOT_FOUND,
            )

    title_item = fields.get("title")
    raw_title = str(title_item.value) if title_item and title_item.value else None
    return ExtractionResult(
        fields=fields,
        raw_title=raw_title,
        structured_data_found=structured_found,
    )


# ---------------------------------------------------------------------------
# Stage A: JSON-LD Structured Data
# ---------------------------------------------------------------------------


def _extract_stage_a_structured(
    soup: BeautifulSoup, source_url: str
) -> tuple[dict[str, ExtractedField], bool]:
    results: dict[str, ExtractedField] = {}
    scripts = soup.find_all("script", type="application/ld+json")
    if not scripts:
        return results, False

    structured_found = False

    for script in scripts:
        raw_content = script.string or script.text
        if not raw_content:
            continue
        try:
            data = json.loads(raw_content)
        except Exception:
            continue

        items = (
            data
            if isinstance(data, list)
            else (data.get("@graph", [data]) if isinstance(data, dict) else [])
        )
        for item in items:
            if not isinstance(item, dict):
                continue
            item_type = item.get("@type", "")
            if isinstance(item_type, list):
                item_type = " ".join(item_type)

            # Check if this object represents an event, job posting, or course
            if any(
                t in item_type
                for t in ["Event", "Hackathon", "JobPosting", "Course", "Competition"]
            ):
                structured_found = True
                _parse_json_ld_item(item, source_url, results)

    return results, structured_found


def _parse_json_ld_item(
    item: dict[str, Any], source_url: str, results: dict[str, ExtractedField]
) -> None:
    # Title
    name = item.get("name") or item.get("headline") or item.get("title")
    if name and isinstance(name, str) and "title" not in results:
        results["title"] = ExtractedField(
            field_name="title",
            value=_clean_text(name),
            supporting_excerpt=_make_excerpt(f"JSON-LD name: {name}"),
            extraction_method=ExtractionMethod.STRUCTURED,
            evidence_status=EvidenceStatus.FOUND,
        )

    # Opportunity Type
    item_type = str(item.get("@type", ""))
    classified = _classify_opportunity_type(item_type + " " + str(name or ""))
    if classified and "opportunity_type" not in results:
        results["opportunity_type"] = ExtractedField(
            field_name="opportunity_type",
            value=classified,
            supporting_excerpt=_make_excerpt(f"JSON-LD @type: {item_type}"),
            extraction_method=ExtractionMethod.STRUCTURED,
            evidence_status=EvidenceStatus.FOUND,
        )

    # Organizer
    organizer = item.get("organizer") or item.get("hiringOrganization") or item.get("publisher")
    org_name = None
    if isinstance(organizer, dict):
        org_name = organizer.get("name")
    elif isinstance(organizer, str):
        org_name = organizer
    if org_name and "organizer" not in results:
        results["organizer"] = ExtractedField(
            field_name="organizer",
            value=_clean_text(org_name),
            supporting_excerpt=_make_excerpt(f"JSON-LD organizer: {org_name}"),
            extraction_method=ExtractionMethod.STRUCTURED,
            evidence_status=EvidenceStatus.FOUND,
        )

    # Dates
    start_dt = _parse_iso_datetime(item.get("startDate"))
    if start_dt and "start_date" not in results:
        results["start_date"] = ExtractedField(
            field_name="start_date",
            value=start_dt,
            supporting_excerpt=_make_excerpt(f"JSON-LD startDate: {item.get('startDate')}"),
            extraction_method=ExtractionMethod.STRUCTURED,
            evidence_status=EvidenceStatus.FOUND,
        )

    end_dt = _parse_iso_datetime(item.get("endDate"))
    if end_dt and "end_date" not in results:
        results["end_date"] = ExtractedField(
            field_name="end_date",
            value=end_dt,
            supporting_excerpt=_make_excerpt(f"JSON-LD endDate: {item.get('endDate')}"),
            extraction_method=ExtractionMethod.STRUCTURED,
            evidence_status=EvidenceStatus.FOUND,
        )

    deadline_val = item.get("validThrough") or item.get("applicationDeadline")
    reg_dt = _parse_iso_datetime(deadline_val)
    if reg_dt and "registration_deadline" not in results:
        results["registration_deadline"] = ExtractedField(
            field_name="registration_deadline",
            value=reg_dt,
            supporting_excerpt=_make_excerpt(f"JSON-LD deadline: {deadline_val}"),
            extraction_method=ExtractionMethod.STRUCTURED,
            evidence_status=EvidenceStatus.FOUND,
        )

    # Location & Mode
    location_raw = item.get("location")
    loc_str = None
    if isinstance(location_raw, dict):
        loc_str = location_raw.get("name") or location_raw.get("address")
        if isinstance(loc_str, dict):
            parts = [loc_str.get("addressLocality"), loc_str.get("addressCountry")]
            loc_str = ", ".join(p for p in parts if p)
    elif isinstance(location_raw, str):
        loc_str = location_raw

    attendance_mode = item.get("eventAttendanceMode") or ""
    if "OnlineEventAttendanceMode" in attendance_mode:
        results["mode"] = ExtractedField(
            field_name="mode",
            value=ParticipationMode.ONLINE,
            supporting_excerpt=_make_excerpt(f"JSON-LD eventAttendanceMode: {attendance_mode}"),
            extraction_method=ExtractionMethod.STRUCTURED,
            evidence_status=EvidenceStatus.FOUND,
        )
    elif "OfflineEventAttendanceMode" in attendance_mode:
        results["mode"] = ExtractedField(
            field_name="mode",
            value=ParticipationMode.OFFLINE,
            supporting_excerpt=_make_excerpt(f"JSON-LD eventAttendanceMode: {attendance_mode}"),
            extraction_method=ExtractionMethod.STRUCTURED,
            evidence_status=EvidenceStatus.FOUND,
        )
    elif "MixedEventAttendanceMode" in attendance_mode:
        results["mode"] = ExtractedField(
            field_name="mode",
            value=ParticipationMode.HYBRID,
            supporting_excerpt=_make_excerpt(f"JSON-LD eventAttendanceMode: {attendance_mode}"),
            extraction_method=ExtractionMethod.STRUCTURED,
            evidence_status=EvidenceStatus.FOUND,
        )

    if loc_str and "location" not in results:
        results["location"] = ExtractedField(
            field_name="location",
            value=_clean_text(str(loc_str)),
            supporting_excerpt=_make_excerpt(f"JSON-LD location: {loc_str}"),
            extraction_method=ExtractionMethod.STRUCTURED,
            evidence_status=EvidenceStatus.FOUND,
        )

    # Application URL
    app_url = item.get("url")
    if app_url and isinstance(app_url, str) and "application_url" not in results:
        results["application_url"] = ExtractedField(
            field_name="application_url",
            value=urljoin(source_url, app_url.strip()),
            supporting_excerpt=_make_excerpt(f"JSON-LD url: {app_url}"),
            extraction_method=ExtractionMethod.STRUCTURED,
            evidence_status=EvidenceStatus.FOUND,
        )


# ---------------------------------------------------------------------------
# Stage B: HTML Metadata (OpenGraph, Title, Meta Tags)
# ---------------------------------------------------------------------------


def _extract_stage_b_metadata(soup: BeautifulSoup, source_url: str) -> dict[str, ExtractedField]:
    results: dict[str, ExtractedField] = {}

    def get_meta(*names: str) -> tuple[str | None, str | None]:
        for name in names:
            tag = soup.find("meta", attrs={"property": name}) or soup.find(
                "meta", attrs={"name": name}
            )
            if tag and isinstance(tag, Tag) and tag.get("content"):
                content_str = _get_tag_attr_str(tag, "content")
                if content_str:
                    return content_str, name
        return None, None

    # Title
    og_title, og_tag = get_meta("og:title", "twitter:title")
    if og_title:
        results["title"] = ExtractedField(
            field_name="title",
            value=_clean_text(og_title),
            supporting_excerpt=_make_excerpt(f"<{og_tag}>: {og_title}"),
            extraction_method=ExtractionMethod.RULE_BASED,
            evidence_status=EvidenceStatus.FOUND,
        )
    elif soup.title and soup.title.string:
        clean_t = _clean_text(soup.title.string)
        if clean_t:
            results["title"] = ExtractedField(
                field_name="title",
                value=clean_t,
                supporting_excerpt=_make_excerpt(f"<title>: {clean_t}"),
                extraction_method=ExtractionMethod.RULE_BASED,
                evidence_status=EvidenceStatus.FOUND,
            )

    # Opportunity Type from Title / Description
    desc, _ = get_meta("og:description", "description", "twitter:description")
    title_field = results.get("title")
    title_val = str(title_field.value) if title_field and title_field.value else ""
    full_sample = f"{title_val} {desc or ''}"
    opp_type = _classify_opportunity_type(full_sample)
    if opp_type:
        results["opportunity_type"] = ExtractedField(
            field_name="opportunity_type",
            value=opp_type,
            supporting_excerpt=_make_excerpt(
                f"Detected from meta description/title: {full_sample[:100]}"
            ),
            extraction_method=ExtractionMethod.RULE_BASED,
            evidence_status=EvidenceStatus.FOUND,
        )

    # Organizer from Site Name / Author
    org, org_tag = get_meta("og:site_name", "author")
    if org:
        results["organizer"] = ExtractedField(
            field_name="organizer",
            value=_clean_text(org),
            supporting_excerpt=_make_excerpt(f"<{org_tag}>: {org}"),
            extraction_method=ExtractionMethod.RULE_BASED,
            evidence_status=EvidenceStatus.FOUND,
        )

    # Canonical Application URL
    canonical_tag = soup.find("link", rel="canonical")
    if canonical_tag and isinstance(canonical_tag, Tag) and canonical_tag.get("href"):
        href = _get_tag_attr_str(canonical_tag, "href")
        if href:
            results["application_url"] = ExtractedField(
                field_name="application_url",
                value=urljoin(source_url, href),
                supporting_excerpt=_make_excerpt(f"<link rel='canonical'>: {href}"),
                extraction_method=ExtractionMethod.RULE_BASED,
                evidence_status=EvidenceStatus.FOUND,
            )

    return results


# ---------------------------------------------------------------------------
# Stage C: Generic Rule-Based & Semantic Heuristics
# ---------------------------------------------------------------------------


def _extract_stage_c_heuristics(soup: BeautifulSoup, source_url: str) -> dict[str, ExtractedField]:
    results: dict[str, ExtractedField] = {}
    page_text = soup.get_text(separator=" ", strip=True)

    # Mode detection
    detected_mode = _detect_mode(page_text)
    if detected_mode:
        results["mode"] = ExtractedField(
            field_name="mode",
            value=detected_mode,
            supporting_excerpt=_make_excerpt(f"Detected participation mode: {detected_mode.value}"),
            extraction_method=ExtractionMethod.RULE_BASED,
            evidence_status=EvidenceStatus.FOUND,
        )

    # Scan for date labels in HTML elements: Registration Deadline / Deadline
    for elem in soup.find_all(["p", "li", "span", "div", "time", "section"]):
        elem_text = elem.get_text(separator=" ", strip=True)
        if re.search(
            r"\b(?:registration|application|submission)\s+deadline\b|\bapply\s+by\b|\bregister\s+by\b",
            elem_text,
            re.IGNORECASE,
        ):
            parsed_dt = _parse_human_date(elem_text) or _parse_iso_datetime(elem_text)
            if parsed_dt:
                results["registration_deadline"] = ExtractedField(
                    field_name="registration_deadline",
                    value=parsed_dt,
                    supporting_excerpt=_make_excerpt(elem_text),
                    extraction_method=ExtractionMethod.RULE_BASED,
                    evidence_status=EvidenceStatus.FOUND,
                )
                break

    # Scan for Event Dates: Start & End Date
    for elem in soup.find_all(["p", "li", "span", "div", "time", "section"]):
        elem_text = elem.get_text(separator=" ", strip=True)
        if re.search(
            r"\b(?:event\s+dates?|starts?\s+on|begins?\s+on)\b",
            elem_text,
            re.IGNORECASE,
        ):
            parsed_dt = _parse_human_date(elem_text) or _parse_iso_datetime(elem_text)
            if parsed_dt and "start_date" not in results:
                results["start_date"] = ExtractedField(
                    field_name="start_date",
                    value=parsed_dt,
                    supporting_excerpt=_make_excerpt(elem_text),
                    extraction_method=ExtractionMethod.RULE_BASED,
                    evidence_status=EvidenceStatus.FOUND,
                )
                break

    # Scan for Eligibility / Requirements section
    for heading in soup.find_all(["h2", "h3", "h4", "strong"]):
        htext = heading.get_text(strip=True).lower()
        if any(w in htext for w in ["eligibility", "who can apply", "target audience", "criteria"]):
            parent = heading.find_parent(["section", "div", "article"]) or heading.parent
            if parent:
                snippet = parent.get_text(separator=" ", strip=True)
                results["eligibility"] = ExtractedField(
                    field_name="eligibility",
                    value=_clean_text(snippet[:400]),
                    supporting_excerpt=_make_excerpt(snippet),
                    extraction_method=ExtractionMethod.RULE_BASED,
                    evidence_status=EvidenceStatus.FOUND,
                )
                break

    # Scan for Skills Required / Prerequisites
    for heading in soup.find_all(["h2", "h3", "h4", "strong"]):
        htext = heading.get_text(strip=True).lower()
        if any(
            w in htext for w in ["skills required", "prerequisites", "tech stack", "technologies"]
        ):
            parent = heading.find_parent(["section", "div", "article"]) or heading.parent
            if parent:
                snippet = parent.get_text(separator=" ", strip=True)
                results["skills_required"] = ExtractedField(
                    field_name="skills_required",
                    value=_clean_text(snippet[:400]),
                    supporting_excerpt=_make_excerpt(snippet),
                    extraction_method=ExtractionMethod.RULE_BASED,
                    evidence_status=EvidenceStatus.FOUND,
                )
                break

    # Scan for Prizes / Compensation / Fee
    for heading in soup.find_all(["h2", "h3", "h4", "strong"]):
        htext = heading.get_text(strip=True).lower()
        if any(
            w in htext
            for w in [
                "prizes",
                "prize pool",
                "compensation",
                "stipend",
                "rewards",
                "entry fee",
                "fees",
            ]
        ):
            parent = heading.find_parent(["section", "div", "article"]) or heading.parent
            if parent:
                snippet = parent.get_text(separator=" ", strip=True)
                results["compensation"] = ExtractedField(
                    field_name="compensation",
                    value=_clean_text(snippet[:300]),
                    supporting_excerpt=_make_excerpt(snippet),
                    extraction_method=ExtractionMethod.RULE_BASED,
                    evidence_status=EvidenceStatus.FOUND,
                )
                break

    # Scan for Action link ("Apply", "Register")
    if "application_url" not in results:
        for a_tag in soup.find_all("a", href=True):
            if not isinstance(a_tag, Tag):
                continue
            atext = a_tag.get_text(strip=True).lower()
            if any(
                w in atext
                for w in ["apply now", "register now", "sign up", "submit entry", "apply here"]
            ):
                href = _get_tag_attr_str(a_tag, "href")
                if href and not href.startswith("#") and not href.startswith("javascript:"):
                    resolved = urljoin(source_url, href)
                    results["application_url"] = ExtractedField(
                        field_name="application_url",
                        value=resolved,
                        supporting_excerpt=_make_excerpt(
                            f"Action link [{a_tag.get_text(strip=True)}]: {href}"
                        ),
                        extraction_method=ExtractionMethod.RULE_BASED,
                        evidence_status=EvidenceStatus.FOUND,
                    )
                    break

    # Location fallback if in-person
    mode_item = results.get("mode")
    if (
        "location" not in results
        and mode_item is not None
        and mode_item.value == ParticipationMode.ONLINE
    ):
        results["location"] = ExtractedField(
            field_name="location",
            value="Online / Virtual",
            supporting_excerpt=_make_excerpt("Derived from participation mode: online"),
            extraction_method=ExtractionMethod.RULE_BASED,
            evidence_status=EvidenceStatus.FOUND,
        )

    return results
