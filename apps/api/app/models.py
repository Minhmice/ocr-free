from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

BackendName = Literal["pipeline", "vlm-auto-engine", "hybrid-auto-engine"]
JobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]


class ConvertOptions(BaseModel):
    backend: BackendName = "pipeline"
    max_pages: int | None = None
    ocr_language: str = "ch"
    enable_table_recognition: bool = True
    enable_formula_recognition: bool = True
    force_ocr: bool = False


class JobRecord(BaseModel):
    job_id: str
    original_file_name: str
    stored_input_path: str
    output_dir: str
    backend: str
    options: dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = "queued"
    progress_message: str = ""
    stdout_tail: list[str] = Field(default_factory=list)
    stderr_tail: list[str] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None


class JobPublic(BaseModel):
    job_id: str = Field(..., alias="jobId")
    file_name: str = Field(..., alias="fileName")
    status: JobStatus
    backend: str
    created_at: str = Field(..., alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt")
    progress_message: str = Field("", alias="progressMessage")
    stdout_tail: list[str] = Field(default_factory=list, alias="stdoutTail")
    stderr_tail: list[str] = Field(default_factory=list, alias="stderrTail")
    error: str | None = None

    model_config = {"populate_by_name": True}


class ConvertResponse(BaseModel):
    job_id: str = Field(..., alias="jobId")
    status: Literal["queued"] = "queued"

    model_config = {"populate_by_name": True}


class AssetRef(BaseModel):
    path: str
    url: str


class ResultPayload(BaseModel):
    markdown: str = ""
    markdown_plain: str = Field("", alias="markdownPlain")
    json: dict[str, Any] | list[Any] | Any = Field(default_factory=dict)
    assets: list[AssetRef] = Field(default_factory=list)
    download_url: str = Field("", alias="downloadUrl")

    model_config = {"populate_by_name": True}
