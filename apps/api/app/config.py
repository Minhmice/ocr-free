from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_repo_root() -> Path:
    """apps/api/app/config.py -> repo root is parents[2] (app → api → apps → repo)."""
    here = Path(__file__).resolve().parent
    return here.parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MINERU_API_", env_file=".env", extra="ignore")

    repo_root: Path = Field(default_factory=_find_repo_root)
    data_dir: Path | None = None
    max_upload_mb: int = 512

    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def resolved_data_dir(self) -> Path:
        base = self.data_dir or (self.repo_root / "data")
        return base.resolve()

    @property
    def uploads_dir(self) -> Path:
        return self.resolved_data_dir / "uploads"

    @property
    def outputs_dir(self) -> Path:
        return self.resolved_data_dir / "outputs"

    @property
    def jobs_dir(self) -> Path:
        return self.resolved_data_dir / "jobs"

    @property
    def models_dir(self) -> Path:
        return self.resolved_data_dir / "models"

    @property
    def hf_home(self) -> Path:
        return self.models_dir / "huggingface"

    @property
    def xdg_cache_home(self) -> Path:
        return self.models_dir / "cache"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.data_dir is None:
        s.data_dir = s.repo_root / "data"
    return s
