"""Wraps a plain-text email body in an HTML layout that matches the app's
own design system (frontend/app/globals.css) - same brand color, font, card
radius, and border color as the dashboard, not a generic template.

The app's tokens are defined in OKLCH, which email clients don't render -
these are the same tokens pre-converted to sRGB hex:
  --primary            oklch(58% .2 285)   -> #735fe9
  --primary-foreground oklch(99% .005 285) -> #fbfbff
  --foreground         oklch(24% .03 285)  -> #1e1d2d
  --muted-foreground   oklch(58% .02 285)  -> #797986
  --border             oklch(92.5% .006 285) -> #e6e6ea
  --background         oklch(97.5% .004 285) -> #f6f6f9
  --card               oklch(100% 0 0)     -> #ffffff
  --radius             0.75rem             -> 12px
Font: Plus Jakarta Sans (same as the app), with a system-font fallback
stack for clients that block the Google Fonts request.
"""

from html import escape as _escape

SIGNATURE_NAME = "Adil Ishtiaq"
SIGNATURE_COMPANY = "NexCraft Solutions"
SIGNATURE_WEBSITE = "https://nexcraftsolutions.com/"

PLAIN_SIGNATURE = f"\n\n{SIGNATURE_NAME}\n{SIGNATURE_COMPANY}\n{SIGNATURE_WEBSITE}"

_PRIMARY = "#735fe9"
_PRIMARY_FOREGROUND = "#fbfbff"
_FOREGROUND = "#1e1d2d"
_MUTED_FOREGROUND = "#797986"
_BORDER = "#e6e6ea"
_BACKGROUND = "#f6f6f9"
_CARD = "#ffffff"
_RADIUS = "12px"
_FONT_STACK = (
    "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', "
    "Roboto, Arial, sans-serif"
)


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

    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  </head>
  <body style="margin:0;padding:0;background-color:{_BACKGROUND};">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{_BACKGROUND};padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">
            <tr>
              <td style="padding:0 4px 20px 4px;">
                <table role="presentation" cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="width:32px;height:32px;background-color:{_PRIMARY};border-radius:8px;text-align:center;">
                      <span style="display:block;color:{_PRIMARY_FOREGROUND};font-family:{_FONT_STACK};font-size:13px;font-weight:700;line-height:32px;">NC</span>
                    </td>
                    <td style="padding-left:10px;font-family:{_FONT_STACK};">
                      <span style="font-size:14px;font-weight:600;color:{_FOREGROUND};">{_escape(SIGNATURE_COMPANY)}</span>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="background-color:{_CARD};border:1px solid {_BORDER};border-radius:{_RADIUS};padding:32px;font-family:{_FONT_STACK};color:{_FOREGROUND};font-size:15px;line-height:1.65;">
                {paragraphs_html}
                <div style="margin-top:8px;padding-top:20px;border-top:1px solid {_BORDER};">
                  <p style="margin:0;font-weight:600;color:{_FOREGROUND};">{_escape(SIGNATURE_NAME)}</p>
                  <p style="margin:2px 0 0 0;color:{_MUTED_FOREGROUND};font-size:14px;">{_escape(SIGNATURE_COMPANY)}</p>
                  <p style="margin:6px 0 0 0;">
                    <a href="{SIGNATURE_WEBSITE}" style="color:{_PRIMARY};text-decoration:none;font-size:14px;font-weight:500;">nexcraftsolutions.com</a>
                  </p>
                </div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""
