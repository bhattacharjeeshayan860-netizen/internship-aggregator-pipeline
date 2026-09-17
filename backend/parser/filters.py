"""Job filtering logic — internship type, paid status, geography, language, domain."""
from __future__ import annotations

import re
from urllib.parse import urlparse

# ── Regex patterns ───────────────────────────────────────────────────────────

INTERNSHIP_RE = re.compile(
    r"\b(intern(ship)?|co[‑\-\s]?op|placement|trainee|apprentice)\b",
    re.IGNORECASE,
)

UNPAID_RE = re.compile(
    r"\b(unpaid|volunteer|uncompensated|no[\s\-]?stipend|no[\s\-]?compensation|"
    r"pro[\s\-]?bono|honorarium only|academic credit only)\b",
    re.IGNORECASE,
)

VALID_GEO_RE = re.compile(
    r"\b(canada|canadian|usa?|united states|new york|san francisco|seattle|boston|"
    r"austin|chicago|toronto|vancouver|montreal|calgary|"
    r"uk|united kingdom|england|london|scotland|wales|"
    r"germany|berlin|munich|france|paris|netherlands|amsterdam|"
    r"spain|madrid|ireland|dublin|sweden|stockholm|denmark|copenhagen|"
    r"norway|finland|switzerland|austria|belgium|poland|portugal|"
    r"europe|european union|\beu\b|"
    r"singapore|remote|worldwide|anywhere|global|international)\b",
    re.IGNORECASE,
)

INDIA_RE = re.compile(r"\bindia\b", re.IGNORECASE)

SPAM_DOMAINS = frozenset({
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
    "clickfunnels.com", "wix.com", "wordpress.com", "blogspot.com",
    "forms.gle", "docs.google.com",
})

# ── Non-technical role filter ─────────────────────────────────────────────────
# Roles that contain "intern" in the title but are NOT DS/ML/SWE-relevant.
# Match means REJECT the job.

NON_TECH_TITLE_RE = re.compile(
    r"\b("
    # Finance / Accounting
    r"account(ing|ant|s\s+payable|s\s+receivable)?(?!\s+engineer|\s+data)"
    r"|audit|tax\s+(operation|intern|analyst|coord)"
    r"|controller|bookkeep|strategic\s+finance|financial\s+planning"
    r"|finance\s+operation|treasury|actuari"
    # Sales / Marketing / Comms
    r"|sales(?!\s+engineer)"
    r"|marketing(?!\s+(tech|analytics|data|engineer))"
    r"|business\s+development|growth\s+market|growth\s+hack"
    r"|public\s+relations|\bpr\s+intern"
    r"|communications\s+intern|copywriting|content\s+(writer|creator|market)"
    # HR / People / Recruiting
    r"|\bhr\s+(intern|analyst)|human\s+resources"
    r"|people\s+(partner|experience)|employee\s+(experience|workplace)"
    r"|recruiter|recruiting\s+coord|talent\s+(acqui|coord|recruit)"
    r"|learning\s+(&|and)\s+development|\bl&d\b"
    # Design (non-product / non-UX-engineering)
    r"|brand\s+design|graphic\s+design|visual\s+design|motion\s+design"
    # Legal / Compliance (non-security)
    r"|legal\s+intern|paralegal|general\s+counsel"
    r"|compliance\s+specialist|compliance\s+coord"
    # Non-tech Operations
    r"|vendor\s+manag|supply\s+chain|procurement"
    r"|brokerage\s+operation|crypto\s+operation|crypto\s+partnership"
    r"|futures\s+.*operation|prediction\s+market\s+operation"
    r"|brokerage\s+risk\s+analyst"  # pure ops risk, not quant
    # Admin / Coordination
    r"|early\s+talent\s+recruiting|emerging\s+talent\s+recruit"
    r"|admin(?:istrative)?\s+intern|office\s+manager|executive\s+assistant"
    r"|it\s+support\s+technician"
    r")\b",
    re.IGNORECASE,
)

# Full-time seniority levels — reject anything starting with these
SENIORITY_START_RE = re.compile(
    r"^(senior|sr\.|lead|principal|staff|director|manager|"
    r"head\s+of|vp\b|vice\s+president|president|cto|ceo|coo)\b",
    re.IGNORECASE,
)


# ── Filter functions ─────────────────────────────────────────────────────────


def is_internship(title: str, description: str = "") -> bool:
    """True if the role title or opening of description signals an internship."""
    return bool(
        INTERNSHIP_RE.search(title)
        or INTERNSHIP_RE.search(description[:800])
    )


def is_paid(description: str) -> bool:
    """True unless the description explicitly signals an unpaid position."""
    return not bool(UNPAID_RE.search(description))


def is_valid_geo(location: str, description: str = "") -> bool:
    """
    Passes if:
    - The location is Remote / Global
    - The location is a valid target geography (CA, US, UK, EU, SG)
    - The location is India (on-site India is acceptable per spec)
    - Location is blank (unknown — pass through to avoid false negatives)
    """
    if not location.strip():
        return True  # unknown location — don't discard

    loc_lower = location.lower()

    # Remote variants always pass
    if any(t in loc_lower for t in ("remote", "anywhere", "global", "worldwide")):
        return True

    # India on-site is explicitly allowed
    if INDIA_RE.search(location):
        return True

    # Valid target geographies
    if VALID_GEO_RE.search(location):
        return True

    return False


def is_english(text: str) -> bool:
    """
    Heuristic: if >80% of characters are printable ASCII, assume English.
    Handles HTML entities, code blocks, etc. gracefully.
    """
    if not text or len(text) < 20:
        return True
    sample = text[:500]
    ascii_count = sum(1 for c in sample if ord(c) < 128)
    return (ascii_count / len(sample)) > 0.80


def has_valid_domain(url: str) -> bool:
    """Reject empty URLs, bare IPs, localhost, and known spam domains."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        if not host or host == "localhost":
            return False
        # Bare IPv4
        if re.match(r"^(\d{1,3}\.){3}\d{1,3}(:\d+)?$", host):
            return False
        if host in SPAM_DOMAINS:
            return False
        return "." in host
    except Exception:
        return False


def is_relevant_domain(title: str) -> bool:
    """
    Reject roles that are clearly non-technical (accounting, sales, HR, etc.)
    or full-time seniority roles that slip through the internship filter.
    """
    if SENIORITY_START_RE.search(title.strip()):
        return False
    if NON_TECH_TITLE_RE.search(title):
        return False
    return True


def determine_work_mode(location: str, description: str = "") -> str:
    """Classify work mode from location string and description context."""
    text = f"{location} {description[:500]}".lower()
    if "remote" in text:
        return "Remote"
    if "hybrid" in text:
        return "Hybrid"
    return "On-site"


def passes_all_filters(job: dict) -> bool:
    """
    Master filter gate — returns True only if the job passes every check:
    internship type, paid, geography, English, valid domain, relevant domain.
    """
    title = job.get("title", "")
    description = job.get("description", "")
    location = job.get("location", "")
    apply_url = job.get("apply_url", "")

    return (
        is_internship(title, description)
        and is_paid(description)
        and is_valid_geo(location, description)
        and is_english(title + " " + description[:300])
        and has_valid_domain(apply_url)
        and is_relevant_domain(title)
    )
