import os
import json
from pathlib import Path

class Config:
    _instance = None
    _SETUP_COMMAND = (
        "Set SMART_SEARCH_API_URL and SMART_SEARCH_API_KEY in the environment, then run "
        "`smart-search doctor --format json`. Optional: set EXA_API_KEY, "
        "TAVILY_API_KEY, and FIRECRAWL_API_KEY for additional providers."
    )
    _DEFAULT_MODEL = "grok-4-fast"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config_file = None
            cls._instance._cached_model = None
        return cls._instance

    @property
    def config_file(self) -> Path:
        if self._config_file is None:
            config_dir = Path.home() / ".config" / "smart-search"
            try:
                config_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                config_dir = Path.cwd() / ".smart-search"
                config_dir.mkdir(parents=True, exist_ok=True)
            self._config_file = config_dir / "config.json"
        return self._config_file

    def _load_config_file(self) -> dict:
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_config_file(self, config_data: dict) -> None:
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise ValueError(f"无法保存配置文件: {str(e)}")

    @property
    def debug_enabled(self) -> bool:
        return os.getenv("SMART_SEARCH_DEBUG", "false").lower() in ("true", "1", "yes")

    @property
    def retry_max_attempts(self) -> int:
        return int(os.getenv("SMART_SEARCH_RETRY_MAX_ATTEMPTS", "3"))

    @property
    def retry_multiplier(self) -> float:
        return float(os.getenv("SMART_SEARCH_RETRY_MULTIPLIER", "1"))

    @property
    def retry_max_wait(self) -> int:
        return int(os.getenv("SMART_SEARCH_RETRY_MAX_WAIT", "10"))

    @property
    def smart_search_api_url(self) -> str:
        url = os.getenv("SMART_SEARCH_API_URL")
        if not url:
            raise ValueError(
                f"OpenAI-compatible API URL 未配置！\n"
                f"请配置 CLI 环境变量：\n{self._SETUP_COMMAND}"
            )
        return url

    @property
    def smart_search_api_key(self) -> str:
        key = os.getenv("SMART_SEARCH_API_KEY")
        if not key:
            raise ValueError(
                f"OpenAI-compatible API Key 未配置！\n"
                f"请配置 CLI 环境变量：\n{self._SETUP_COMMAND}"
            )
        return key

    @property
    def tavily_enabled(self) -> bool:
        return os.getenv("TAVILY_ENABLED", "true").lower() in ("true", "1", "yes")

    @property
    def tavily_api_url(self) -> str:
        return os.getenv("TAVILY_API_URL", "https://api.tavily.com")

    @property
    def tavily_api_key(self) -> str | None:
        return os.getenv("TAVILY_API_KEY")

    @property
    def firecrawl_api_url(self) -> str:
        return os.getenv("FIRECRAWL_API_URL", "https://api.firecrawl.dev/v2")

    @property
    def firecrawl_api_key(self) -> str | None:
        return os.getenv("FIRECRAWL_API_KEY")

    @property
    def log_level(self) -> str:
        return os.getenv("SMART_SEARCH_LOG_LEVEL", "INFO").upper()

    @property
    def log_dir(self) -> Path:
        log_dir_str = os.getenv("SMART_SEARCH_LOG_DIR", "logs")
        log_dir = Path(log_dir_str)
        if log_dir.is_absolute():
            return log_dir

        home_log_dir = Path.home() / ".config" / "smart-search" / log_dir_str
        try:
            home_log_dir.mkdir(parents=True, exist_ok=True)
            return home_log_dir
        except OSError:
            pass

        cwd_log_dir = Path.cwd() / log_dir_str
        try:
            cwd_log_dir.mkdir(parents=True, exist_ok=True)
            return cwd_log_dir
        except OSError:
            pass

        tmp_log_dir = Path("/tmp") / "smart-search" / log_dir_str
        tmp_log_dir.mkdir(parents=True, exist_ok=True)
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
            or self._load_config_file().get("model")
            or self._DEFAULT_MODEL
        )
        self._cached_model = self._apply_model_suffix(model)
        return self._cached_model

    def set_model(self, model: str) -> None:
        config_data = self._load_config_file()
        config_data["model"] = model
        self._save_config_file(config_data)
        self._cached_model = self._apply_model_suffix(model)

    @staticmethod
    def _mask_api_key(key: str) -> str:
        if not key or len(key) <= 8:
            return "***"
        return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"

    @property
    def output_cleanup_enabled(self) -> bool:
        return os.getenv("SMART_SEARCH_OUTPUT_CLEANUP", "true").lower() in ("true", "1", "yes")

    @property
    def log_to_file_enabled(self) -> bool:
        return os.getenv("SMART_SEARCH_LOG_TO_FILE", "false").lower() in ("true", "1", "yes")

    @property
    def ssl_verify_enabled(self) -> bool:
        return os.getenv("SSL_VERIFY", "true").lower() not in ("false", "0", "no")

    @property
    def exa_api_key(self) -> str | None:
        return os.getenv("EXA_API_KEY")

    @property
    def exa_base_url(self) -> str:
        return os.getenv("EXA_BASE_URL", "https://api.exa.ai")

    @property
    def exa_timeout(self) -> float:
        return float(os.getenv("EXA_TIMEOUT_SECONDS", "30"))

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

        return {
            "SMART_SEARCH_API_URL": api_url,
            "SMART_SEARCH_API_KEY": api_key_masked,
            "SMART_SEARCH_MODEL": self.smart_search_model,
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
            "config_status": config_status
        }

config = Config()
