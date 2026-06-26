from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class LinkCardRequest(BaseModel):
    url: str
    title: str = ""
    description: str = ""
    image_url: str = ""


class LinkCardResponse(BaseModel):
    html: str


class TweetRequest(BaseModel):
    text: str = ""
    file_name: str = ""
    provider_index: int | None = None
    model: str | None = None


class TweetResponse(BaseModel):
    tweets: list[str]
    warning: str | None = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    context: str = ""
    provider_index: int | None = None
    model: str | None = None


class WikiFile(BaseModel):
    name: str
    title: str


class WikiContent(BaseModel):
    name: str
    title: str
    content: str


class DashboardAppStatus(BaseModel):
    name: str
    icon: str
    description: str
    last_used: str | None = None
    status: str = "ready"


class TelegramDigestStatus(BaseModel):
    running: bool
    last_run: str | None = None
    messages_processed: int = 0
    emails_sent: int = 0


class TelegramDigestRunResult(BaseModel):
    timestamp: str
    messages_found: int
    messages_processed: int
    emails_sent: int
    errors: list[str]


class TelegramFilesStatus(BaseModel):
    running: bool
    last_run: str | None = None
    files_saved: int = 0


class TelegramFilesRunResult(BaseModel):
    timestamp: str
    files_found: int
    files_saved: int
    duplicates_skipped: int
    errors: list[str]


class CronJobStatus(BaseModel):
    job_id: str
    name: str
    app: str
    cron_expression: str
    enabled: bool
    next_run: str | None = None
    last_run: str | None = None
    total_runs: int = 0
    last_result: dict | None = None


class CronJobUpdate(BaseModel):
    cron_expression: str | None = None
    enabled: bool | None = None
