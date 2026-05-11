from pathlib import Path

import pytest

from smart_search.config import Config


def _fresh_config_file(monkeypatch):
    config = Config()
    monkeypatch.setattr(config, "_config_file", None)
    return config


def test_env_dir_overrides_config_file_path(monkeypatch, tmp_path):
    target = tmp_path / "custom-config-root"
    monkeypatch.setenv("SMART_SEARCH_CONFIG_DIR", str(target))
    config = _fresh_config_file(monkeypatch)
    assert config.config_file == target / "config.json"
    assert target.exists() and target.is_dir()


def test_env_dir_pointing_at_unwritable_does_not_crash(monkeypatch, tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file, not a directory")
    bogus = blocker / "child"
    monkeypatch.setenv("SMART_SEARCH_CONFIG_DIR", str(bogus))
    config = _fresh_config_file(monkeypatch)
    assert config.config_file == bogus / "config.json"
    assert config._load_config_file() == {}


def test_no_env_falls_back_to_home(monkeypatch, tmp_path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    config = _fresh_config_file(monkeypatch)
    assert config.config_file == fake_home / ".config" / "smart-search" / "config.json"


def test_env_dir_also_governs_log_dir_parent(monkeypatch, tmp_path):
    target = tmp_path / "shared-root"
    monkeypatch.setenv("SMART_SEARCH_CONFIG_DIR", str(target))
    config = _fresh_config_file(monkeypatch)
    assert config.log_dir == target / "logs"
    assert (target / "logs").is_dir()


def test_save_unwritable_raises_with_hint(monkeypatch, tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file")
    bogus = blocker / "child"
    monkeypatch.setenv("SMART_SEARCH_CONFIG_DIR", str(bogus))
    config = _fresh_config_file(monkeypatch)
    with pytest.raises(ValueError) as exc:
        config._save_config_file({"x": 1})
    assert "无法保存" in str(exc.value)
