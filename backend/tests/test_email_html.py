from app.services.email_html import (
    SIGNATURE_COMPANY,
    SIGNATURE_NAME,
    SIGNATURE_WEBSITE,
    append_signature,
    render_html_email,
)


def test_append_signature_adds_real_identity():
    result = append_signature("Hi there,\n\nQuick note about your site.")
    assert SIGNATURE_NAME in result
    assert SIGNATURE_COMPANY in result
    assert SIGNATURE_WEBSITE in result


def test_render_html_email_escapes_body_content():
    html = render_html_email(append_signature("Body with <script>alert(1)</script> in it."))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_render_html_email_renders_signature_as_real_link():
    html = render_html_email(append_signature("Hi there,\n\nQuick note."))
    assert f'<a href="{SIGNATURE_WEBSITE}"' in html
    assert SIGNATURE_NAME in html
    assert SIGNATURE_COMPANY in html


def test_render_html_email_preserves_paragraph_breaks():
    html = render_html_email(append_signature("First paragraph.\n\nSecond paragraph."))
    assert "First paragraph." in html
    assert "Second paragraph." in html
    assert html.count("<p") >= 2
