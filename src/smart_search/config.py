import json
import os
from pathlib import Path
from urllib.parse import urlparse

class Config:
    _instance = None
    _SETUP_COMMAND = (
        "Run `smart-search setup`, or set SMART_SEARCH_API_URL and "
        "SMART_SEARCH_API_KEY in the environment, then run "
        "`smart-search doctor --format json`."
    )
    _DEFAULT_MODEL = "grok-4-fast"
    _DEFAULT_API_MODE = "auto"
    _DEFAULT_XAI_TOOLS = "web_search,x_search"
    _ALLOWED_API_MODES = {"auto", "xai-responses", "chat-completions"}
    _ALLOWED_XAI_TOOLS = {"web_search", "x_search"}
    _CONFIG_KEYS = {
        "SMART_SEARCH_API_URL",
        "SMART_SEARCH_API_KEY",
        "SMART_SEARCH_API_MODE",
        "SMART_SEARCH_XAI_TOOLS",
        "SMART_SEARCH_MODEL",
        "EXA_API_KEY",
        "EXA_BASE_URL",
        "EXA_TIMEOUT_SECONDS",
        "TAVILY_API_KEY",
        "TAVILY_API_URL",
        "TAVILY_ENABLED",
        "FIRECRAWL_API_KEY",
        "FIRECRAWL_API_URL",
        "SMART_SEARCH_DEBUG",
        "SMART_SEARCH_LOG_LEVEL",
        "SMART_SEARCH_LOG_DIR",
        "SMART_SEARCH_RETRY_MAX_ATTEMPTS",
        "SMART_SEARCH_RETRY_MULTIPLIER",
        "SMART_SEARCH_RETRY_MAX_WAIT",
        "SMART_SEARCH_OUTPUT_CLEANUP",
        "SMART_SEARCH_LOG_TO_FILE",
        "SSL_VERIFY",
    }
    _LEGACY_CONFIG_KEYS = {"model": "SMART_SEARCH_MODEL"}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config_file = None
            cls._instance._cached_model = None
        return cls._instance

    @staticmethod
    def _resolve_config_dir() -> tuple[Path, bool]:
        env_dir = os.getenv("SMART_SEARCH_CONFIG_DIR")
        if env_dir:
            return Path(env_dir).expanduser(), True
        return Path.home() / ".config" / "smart-search", False

    @staticmethod
    def _safe_mkdir(p: Path) -> bool:
        try:
            p.mkdir(parents=True, exist_ok=True)
            return True
        except (PermissionError, OSError):
            return False

    @property
    def config_file(self) -> Path:
        if self._config_file is None:
            config_dir, env_pinned = self._resolve_config_dir()
            ok = self._safe_mkdir(config_dir)
            if not env_pinned and not ok:
                cwd_dir = Path.cwd() / ".smart-search"
                if self._safe_mkdir(cwd_dir):
                    config_dir = cwd_dir
            self._config_file = config_dir / "config.json"
        return self._config_file

    def _load_config_file(self) -> dict:
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (FileNotFoundError, PermissionError, OSError, json.JSONDecodeError):
            return {}

    def _save_config_file(self, config_data: dict) -> None:
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except (IOError, PermissionError, OSError) as e:
            hint = " (sandbox/CI 下可设 SMART_SEARCH_CONFIG_DIR 指向可写目录)" if isinstance(e, PermissionError) else ""
            raise ValueError(f"无法保存配置文件: {str(e)}{hint}")

    def _get_config_value(self, key: str, default: str | None = None) -> str | None:
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value

        data = self._load_config_file()
        value = data.get(key)
        if value is None:
            legacy_key = next((old for old, new in self._LEGACY_CONFIG_KEYS.items() if new == key), None)
            if legacy_key:
                value = data.get(legacy_key)
        if value is None:
            return default
        return str(value)

    def get_saved_config(self, masked: bool = True) -> dict:
        data = self._load_config_file()
        normalized: dict[str, str] = {}
        for old_key, new_key in self._LEGACY_CONFIG_KEYS.items():
            if old_key in data and new_key not in data:
                normalized[new_key] = str(data[old_key])
        for key, value in data.items():
            if key in self._CONFIG_KEYS and value is not None:
                normalized[key] = str(value)
        if not masked:
            return normalized
        return {key: self._mask_if_secret(key, value) for key, value in normalized.items()}

    def get_config_source(self, key: str) -> str:
        if os.getenv(key) is not None:
            return "environment"
        data = self._load_config_file()
        if key in data:
            return "config_file"
        legacy_key = next((old for old, new in self._LEGACY_CONFIG_KEYS.items() if new == key), None)
        if legacy_key and legacy_key in data:
            return "config_file"
        return "default"

    def get_config_sources(self) -> dict[str, str]:
        return {key: self.get_config_source(key) for key in sorted(self._CONFIG_KEYS)}

    def set_config_value(self, key: str, value: str) -> None:
        key = key.strip().upper()
        if key not in self._CONFIG_KEYS:
            raise ValueError(f"Unsupported config key: {key}")
        config_data = self._load_config_file()
        config_data[key] = value
        self._save_config_file(config_data)
        if key in {"SMART_SEARCH_MODEL", "SMART_SEARCH_API_URL", "SMART_SEARCH_API_MODE"}:
            self._cached_model = None

    def unset_config_value(self, key: str) -> None:
        key = key.strip().upper()
        if key not in self._CONFIG_KEYS:
            raise ValueError(f"Unsupported config key: {key}")
        config_data = self._load_config_file()
        config_data.pop(key, None)
        for old_key, new_key in self._LEGACY_CONFIG_KEYS.items():
            if new_key == key:
                config_data.pop(old_key, None)
        self._save_config_file(config_data)
        if key in {"SMART_SEARCH_MODEL", "SMART_SEARCH_API_URL", "SMART_SEARCH_API_MODE"}:
            self._cached_model = None

    def config_path_info(self) -> dict:
        return {"ok": True, "config_file": str(self.config_file), "exists": self.config_file.exists()}

    @property
    def debug_enabled(self) -> bool:
        return (self._get_config_value("SMART_SEARCH_DEBUG", "false") or "false").lower() in ("true", "1", "yes")

    @property
    def retry_max_attempts(self) -> int:
        return int(self._get_config_value("SMART_SEARCH_RETRY_MAX_ATTEMPTS", "3") or "3")

    @property
    def retry_multiplier(self) -> float:
        return float(self._get_config_value("SMART_SEARCH_RETRY_MULTIPLIER", "1") or "1")

    @property
    def retry_max_wait(self) -> int:
        return int(self._get_config_value("SMART_SEARCH_RETRY_MAX_WAIT", "10") or "10")

    @property
    def smart_search_api_url(self) -> str:
        url = self._get_config_value("SMART_SEARCH_API_URL")
        if not url:
            raise ValueError(
                f"Primary API URL 未配置！\n"
                f"请配置 Smart Search：\n{self._SETUP_COMMAND}"
            )
        return url

    @property
    def smart_search_api_key(self) -> str:
        key = self._get_config_value("SMART_SEARCH_API_KEY")
        if not key:
            raise ValueError(
                f"Primary API Key 未配置！\n"
                f"请配置 Smart Search：\n{self._SETUP_COMMAND}"
            )
        return key

    @property
    def smart_search_api_mode(self) -> str:
        return (self._get_config_value("SMART_SEARCH_API_MODE", self._DEFAULT_API_MODE) or self._DEFAULT_API_MODE).strip().lower()

    @property
    def smart_search_xai_tools_raw(self) -> str:
        return self._get_config_value("SMART_SEARCH_XAI_TOOLS", self._DEFAULT_XAI_TOOLS) or self._DEFAULT_XAI_TOOLS

    def resolve_primary_api_mode(self, api_url: str) -> str:
        mode = self.smart_search_api_mode
        if mode not in self._ALLOWED_API_MODES:
            allowed = ", ".join(sorted(self._ALLOWED_API_MODES))
            raise ValueError(f"Invalid SMART_SEARCH_API_MODE: {mode}. Supported values: {allowed}")
        if mode != "auto":
            return mode

        parsed_url = api_url if "://" in api_url else f"https://{api_url}"
        host = (urlparse(parsed_url).hostname or "").lower()
        if host == "api.x.ai":
            return "xai-responses"
        return "chat-completions"

    def parse_xai_tools(self) -> list[str]:
        raw = self.smart_search_xai_tools_raw
        tools: list[str] = []
        invalid: list[str] = []
        seen: set[str] = set()
        for item in raw.split(","):
            tool = item.strip().lower()
            if not tool:
                continue
            if tool not in self._ALLOWED_XAI_TOOLS:
                invalid.append(tool)
                continue
            if tool not in seen:
                seen.add(tool)
                tools.append(tool)
        if invalid:
            allowed = ", ".join(sorted(self._ALLOWED_XAI_TOOLS))
            invalid_text = ", ".join(invalid)
            raise ValueError(f"Invalid SMART_SEARCH_XAI_TOOLS: {invalid_text}. Supported values: {allowed}")
        return tools

    @property
    def tavily_enabled(self) -> bool:
        return (self._get_config_value("TAVILY_ENABLED", "true") or "true").lower() in ("true", "1", "yes")

    @property
    def tavily_api_url(self) -> str:
        return self._get_config_value("TAVILY_API_URL", "https://api.tavily.com") or "https://api.tavily.com"

    @property
    def tavily_api_key(self) -> str | None:
        return self._get_config_value("TAVILY_API_KEY")

    @property
    def firecrawl_api_url(self) -> str:
        return self._get_config_value("FIRECRAWL_API_URL", "https://api.firecrawl.dev/v2") or "https://api.firecrawl.dev/v2"

    @property
    def firecrawl_api_key(self) -> str | None:
        return self._get_config_value("FIRECRAWL_API_KEY")

    @property
    def log_level(self) -> str:
        return (self._get_config_value("SMART_SEARCH_LOG_LEVEL", "INFO") or "INFO").upper()

    @property
    def log_dir(self) -> Path:
        log_dir_str = self._get_config_value("SMART_SEARCH_LOG_DIR", "logs") or "logs"
        log_dir = Path(log_dir_str)
        if log_dir.is_absolute():
            return log_dir

        config_dir, env_pinned = self._resolve_config_dir()
        primary_log_dir = config_dir / log_dir_str
        if self._safe_mkdir(primary_log_dir):
            return primary_log_dir
        if env_pinned:
            return primary_log_dir

        cwd_log_dir = Path.cwd() / log_dir_str
        if self._safe_mkdir(cwd_log_dir):
            return cwd_log_dir

        tmp_log_dir = Path("/tmp") / "smart-search" / log_dir_str
        self._safe_mkdir(tmp_log_dir)
        return tmp_log_dir

    def _apply_model_suffix(self, model: str) -> str:
        try:
            url = self.smart_search_api_url
        except ValueError:
            return model
        if "openrouter" in url and ":online" not in model:
            return f"{model}:online"
        return model

    @property
    def smart_search_model(self) -> str:
        if self._cached_model is not None:
            return self._cached_model

        model = (
            os.getenv("SMART_SEARCH_MODEL")
            or self._get_config_value("SMART_SEARCH_MODEL")
            or self._DEFAULT_MODEL
        )
        self._cached_model = self._apply_model_suffix(model)
        return self._cached_model

    def set_model(self, model: str) -> None:
        self.set_config_value("SMART_SEARCH_MODEL", model)
        self._cached_model = self._apply_model_suffix(model)

    @staticmethod
    def _mask_api_key(key: str) -> str:
        if not key or len(key) <= 8:
            return "***"
        return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"

    @classmethod
    def _mask_if_secret(cls, key: str, value: str) -> str:
        if "KEY" in key or "TOKEN" in key or "SECRET" in key:
            return cls._mask_api_key(value)
        return value

    @property
    def output_cleanup_enabled(self) -> bool:
        return (self._get_config_value("SMART_SEARCH_OUTPUT_CLEANUP", "true") or "true").lower() in ("true", "1", "yes")

    @property
    def log_to_file_enabled(self) -> bool:
        return (self._get_config_value("SMART_SEARCH_LOG_TO_FILE", "false") or "false").lower() in ("true", "1", "yes")

    @property
    def ssl_verify_enabled(self) -> bool:
        return (self._get_config_value("SSL_VERIFY", "true") or "true").lower() not in ("false", "0", "no")

    @property
    def exa_api_key(self) -> str | None:
        return self._get_config_value("EXA_API_KEY")

    @property
    def exa_base_url(self) -> str:
        return self._get_config_value("EXA_BASE_URL", "https://api.exa.ai") or "https://api.exa.ai"

    @property
    def exa_timeout(self) -> float:
        return float(self._get_config_value("EXA_TIMEOUT_SECONDS", "30") or "30")

    def get_config_info(self) -> dict:
        try:
            api_url = self.smart_search_api_url
            api_key_raw = self.smart_search_api_key
            api_key_masked = self._mask_api_key(api_key_raw)
            config_status = "ok: 配置完整"
        except ValueError as e:
            api_url = "未配置"
            api_key_masked = "未配置"
            config_status = f"config_error: {str(e)}"

        smart_search_model = self.smart_search_model
        try:
            primary_api_mode = self.resolve_primary_api_mode(api_url) if api_url != "未配置" else self.smart_search_api_mode
        except ValueError as e:
            primary_api_mode = self.smart_search_api_mode
            if config_status.startswith("ok:"):
                config_status = f"config_error: {str(e)}"

        return {
            "SMART_SEARCH_API_URL": api_url,
            "SMART_SEARCH_API_KEY": api_key_masked,
            "SMART_SEARCH_API_MODE": self.smart_search_api_mode,
            "SMART_SEARCH_XAI_TOOLS": self.smart_search_xai_tools_raw,
            "SMART_SEARCH_MODEL": smart_search_model,
            "SMART_SEARCH_DEBUG": self.debug_enabled,
            "SMART_SEARCH_LOG_LEVEL": self.log_level,
            "SMART_SEARCH_LOG_DIR": str(self.log_dir),
            "SMART_SEARCH_RETRY_MAX_ATTEMPTS": self.retry_max_attempts,
            "SMART_SEARCH_RETRY_MULTIPLIER": self.retry_multiplier,
            "SMART_SEARCH_RETRY_MAX_WAIT": self.retry_max_wait,
            "TAVILY_API_URL": self.tavily_api_url,
            "TAVILY_ENABLED": self.tavily_enabled,
            "TAVILY_API_KEY": self._mask_api_key(self.tavily_api_key) if self.tavily_api_key else "未配置",
            "FIRECRAWL_API_URL": self.firecrawl_api_url,
            "FIRECRAWL_API_KEY": self._mask_api_key(self.firecrawl_api_key) if self.firecrawl_api_key else "未配置",
            "SMART_SEARCH_OUTPUT_CLEANUP": self.output_cleanup_enabled,
            "SMART_SEARCH_LOG_TO_FILE": self.log_to_file_enabled,
            "SSL_VERIFY": self.ssl_verify_enabled,
            "EXA_API_KEY": self._mask_api_key(self.exa_api_key) if self.exa_api_key else "未配置",
            "EXA_BASE_URL": self.exa_base_url,
            "EXA_TIMEOUT_SECONDS": self.exa_timeout,
            "primary_api_mode": primary_api_mode,
            "primary_api_mode_source": self.get_config_source("SMART_SEARCH_API_MODE"),
            "config_file": str(self.config_file),
            "config_sources": self.get_config_sources(),
            "config_status": config_status
        }

config = Config()
