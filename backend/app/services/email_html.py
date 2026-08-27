"""Wraps a plain-text email body in a clean, minimal HTML layout with a
real signature. Keeps the design simple (a single centered card, inline
styles) so it renders reliably across email clients instead of risking
AI-generated markup breaking layout in Outlook/Gmail."""

from html import escape as _escape

SIGNATURE_NAME = "Adil Ishtiaq"
SIGNATURE_COMPANY = "NexCraft Solutions"
SIGNATURE_WEBSITE = "https://nexcraftsolutions.com/"

PLAIN_SIGNATURE = f"\n\n{SIGNATURE_NAME}\n{SIGNATURE_COMPANY}\n{SIGNATURE_WEBSITE}"


def append_signature(body_text: str) -> str:
    return f"{body_text.rstrip()}{PLAIN_SIGNATURE}"


def render_html_email(body_text: str) -> str:
    """body_text should already include the plain-text signature (from
    append_signature) - it's rendered separately, as a real link, rather
    than as plain escaped text."""
    body_text = body_text.strip()
    content = body_text
    if body_text.endswith(PLAIN_SIGNATURE.strip()):
        content = body_text[: -len(PLAIN_SIGNATURE.strip())].rstrip()

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    paragraphs_html = "".join(
        f'<p style="margin:0 0 16px 0;">{_escape(p).replace(chr(10), "<br>")}</p>'
        for p in paragraphs
    )

    signature_html = f"""
                <div style="margin-top:8px;padding-top:16px;border-top:1px solid #e5e7eb;">
                  <p style="margin:0;font-weight:600;">{_escape(SIGNATURE_NAME)}</p>
                  <p style="margin:0;color:#4b5563;">{_escape(SIGNATURE_COMPANY)}</p>
                  <p style="margin:4px 0 0 0;">
                    <a href="{SIGNATURE_WEBSITE}" style="color:#2563eb;text-decoration:none;">{SIGNATURE_WEBSITE}</a>
                  </p>
                </div>"""

    return f"""<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background-color:#f4f4f5;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f5;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;padding:32px;font-family:Arial,Helvetica,sans-serif;color:#1f2937;font-size:15px;line-height:1.6;">
            <tr>
              <td>
                {paragraphs_html}{signature_html}
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""
