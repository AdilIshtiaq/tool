"""Best-effort email discovery by reading a lead's own website.

Google Places never returns email addresses - this is the only automatic
source available. Not every business publishes a findable email; a miss
here is a normal outcome, not an error.
"""

import re

import httpx

REQUEST_TIMEOUT = 8.0
PATHS_TO_TRY = ["", "/contact", "/contact-us"]

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Emails that show up in page source but aren't a real contact address for
# this business - tracking pixels, website-builder platform addresses, etc.
IGNORED_DOMAINS = {
    "sentry.io",
    "wixpress.com",
    "godaddy.com",
    "example.com",
    "domain.com",
    "yourdomain.com",
    "w3.org",
}

IGNORED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")


def _is_usable(email: str) -> bool:
    email = email.lower()
    if email.endswith(IGNORED_EXTENSIONS):
        return False
    domain = email.split("@")[-1]
    return domain not in IGNORED_DOMAINS


def discover_email(website_url: str) -> str | None:
    if not website_url:
        return None

    base = website_url.rstrip("/")
    if not base.startswith(("http://", "https://")):
        base = f"https://{base}"

    for path in PATHS_TO_TRY:
        try:
            response = httpx.get(
                f"{base}{path}",
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; NexCraftLeadBot/1.0)"},
            )
        except httpx.HTTPError:
            continue

        if response.status_code != 200:
            continue

        mailto_matches = re.findall(r'mailto:([^"\'?\s]+)', response.text, re.IGNORECASE)
        for candidate in mailto_matches:
            if _is_usable(candidate):
                return candidate.strip()

        text_matches = EMAIL_REGEX.findall(response.text)
        for candidate in text_matches:
            if _is_usable(candidate):
                return candidate.strip()

    return None
