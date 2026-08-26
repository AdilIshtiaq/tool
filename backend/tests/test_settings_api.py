import app.routers.settings as settings_router_module
import app.services.env_file as env_file_module


def test_update_env_file_preserves_other_lines(tmp_path, monkeypatch):
    """Isolated unit test — never touches the real backend/.env."""
    fake_env = tmp_path / ".env"
    fake_env.write_text(
        "# a comment\nSMTP_HOST=keep.example.com\nOPENAI_API_KEY=keep-me\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(env_file_module, "ENV_PATH", fake_env)

    env_file_module.update_env_file(
        {"SMTP_FROM_NAME": "New Name", "SMTP_HOST": "changed.example.com"}
    )

    content = fake_env.read_text(encoding="utf-8")
    assert "# a comment" in content
    assert "OPENAI_API_KEY=keep-me" in content
    assert "SMTP_HOST=changed.example.com" in content
    assert "SMTP_FROM_NAME=New Name" in content


def test_get_settings_reports_configured_flags_without_leaking_secrets(client):
    response = client.get("/api/settings")
    assert response.status_code == 200
    body = response.json()
    assert "openai_api_key_set" in body
    assert "openai_api_key" not in body
    assert "smtp_password" not in body


def test_update_settings_endpoint_persists_and_reloads(client, monkeypatch):
    """Patches out the disk write itself (never touches real backend/.env)
    and uses monkeypatch.setenv to simulate the reload picking up the change,
    since env vars take priority over .env file values."""
    from app.config import get_settings

    calls = []
    monkeypatch.setattr(settings_router_module, "update_env_file", calls.append)
    monkeypatch.setenv("SMTP_FROM_NAME", "Test Sender")

    response = client.patch("/api/settings", json={"smtp_from_name": "Test Sender"})
    assert response.status_code == 200
    assert response.json()["smtp_from_name"] == "Test Sender"
    assert calls == [{"SMTP_FROM_NAME": "Test Sender"}]
    get_settings.cache_clear()


def test_update_settings_ignores_unset_fields(client, monkeypatch):
    calls = []
    monkeypatch.setattr(settings_router_module, "update_env_file", calls.append)

    response = client.patch("/api/settings", json={"smtp_from_name": "Only This Changes"})
    assert response.status_code == 200
    assert calls == [{"SMTP_FROM_NAME": "Only This Changes"}]
