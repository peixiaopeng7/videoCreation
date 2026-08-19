from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DurationPresetId = Literal["8s", "12s", "15s"]


class CharacterCard(BaseModel):
    id: str
    name: str
    role: str = Field(description="生/旦/配等叙事角色")
    gender: str = ""
    appearance: str
    costume: str
    hair: str
    makeup: str
    personality: str = ""
    mj_prompt: str
    notes: str = ""


class Shot(BaseModel):
    index: int
    duration_sec: float
    template_id: str = ""
    shot_type: str
    action: str
    dialogue: str = ""
    emotion: str = ""
    seedance_prompt: str
    continuity_notes: str = ""


class ShortScript(BaseModel):
    title: str
    logline: str
    duration_sec: int
    theme: str = ""
    conflict: str = ""
    ending_tone: str = ""
    scenes_summary: str = ""
    full_script: str


class ProductionPack(BaseModel):
    id: str
    created_at: str
    source_text: str
    style_pack_id: str
    duration_preset: DurationPresetId
    script: ShortScript
    characters: list[CharacterCard]
    shots: list[Shot]
    mj_prompts_bundle: str = ""
    seedance_prompts_bundle: str = ""
    feedback: Feedback | None = None


class Feedback(BaseModel):
    style_score: int = Field(ge=1, le=5, description="风格像不像")
    character_score: int = Field(ge=1, le=5, description="角色稳不稳")
    motion_score: int = Field(ge=1, le=5, description="动作镜头清不清")
    atmosphere_score: int = Field(ge=1, le=5, description="志怪味")
    notes: str = ""
    video_path: str = ""
    is_gold: bool = False


class StylePack(BaseModel):
    id: str
    name: str
    version: str
    description: str = ""
    aesthetic: dict[str, str] = Field(default_factory=dict)
    positive_keywords_zh: list[str] = Field(default_factory=list)
    positive_keywords_en: list[str] = Field(default_factory=list)
    negative_keywords: list[str] = Field(default_factory=list)
    mj_style_lock: str = ""
    seedance_style_lock: str = ""
    duration_presets: list[dict] = Field(default_factory=list)
    shot_templates: list[dict] = Field(default_factory=list)
    forbidden_notes: list[str] = Field(default_factory=list)


# Resolve forward ref for ProductionPack.feedback
ProductionPack.model_rebuild()
