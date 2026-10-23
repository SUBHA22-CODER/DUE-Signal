from pydantic import BaseModel, Field

class ListDeadlinesInput(BaseModel):
    window_days: int = Field(default=7, ge=1, le=90)

class AddDeadlineInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    course: str = Field(min_length=1, max_length=100)
    due_at: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")
    weight_pct: float = Field(default=0, ge=0, le=100)

class MarkCompleteInput(BaseModel):
    id: int = Field(gt=0)
