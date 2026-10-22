from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Language = Literal["it", "en"]
Score = Annotated[int, Field(strict=True, ge=0, le=100)]
Text = Annotated[str, Field(min_length=1, max_length=2000)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", serialize_by_alias=True)


class Generated(StrictModel):
    prompt: Annotated[str, Field(min_length=1, max_length=300,
        description="One sentence or situation in the requested Italian or English source language.")]
    references: Annotated[list[Text], Field(min_length=1, max_length=3,
        description="Japanese-only translations of the SAME prompt; no English, Italian, romaji, labels or commentary.")]


class Scores(StrictModel):
    grammar: Score
    vocabulary: Score
    register_score: Score = Field(alias="register")
    intent: Score


class Evaluation(StrictModel):
    scores: Scores
    accepted: bool
    explanation: Text
    suggestions: Annotated[list[Text], Field(max_length=8)]
    corrections: Annotated[list[Text], Field(max_length=3)]
    valid_variants: Annotated[list[Text], Field(max_length=3)]


class ExerciseRequest(StrictModel):
    language: Language = "it"
    category: str = Field(default="", max_length=60)
    mode: Literal["new", "review", "cram", "targeted"] = "new"
    generate: bool = False
    difficulty: Literal["easy", "standard", "challenging"] = "standard"


class AnswerRequest(StrictModel):
    exercise_id: str = Field(min_length=1, max_length=64)
    answer: str = Field(min_length=1, max_length=500)
    hinted: bool = False


class Settings(StrictModel):
    language: Language = "it"
    ui_language: Language = "it"
    category: str = Field(default="", max_length=60)
    generation_provider: Literal["openai", "openrouter"] = "openai"
    evaluation_provider: Literal["openai", "openrouter"] = "openai"
    generation_model: str = Field(default="local-model", min_length=1, max_length=200)
    evaluation_model: str = Field(default="local-model", min_length=1, max_length=200)
    generation_temperature: float = Field(default=0.2, ge=0, le=2)
    evaluation_temperature: float = Field(default=0.2, ge=0, le=2)
    generation_max_tokens: int = Field(default=2000, ge=128, le=8192)
    evaluation_max_tokens: int = Field(default=2000, ge=128, le=8192)
    openai_base_url: str = Field(default="http://localhost:1234/v1", min_length=1, max_length=500)
    openai_api_key: str = Field(default="", max_length=1000, exclude=True, repr=False)
    openrouter_api_key: str = Field(default="", max_length=1000, exclude=True, repr=False)
    mcp_enabled: bool = False
