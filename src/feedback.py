from __future__ import annotations

from .models import Feedback, ProductionPack
from .storage import load_history, save_gold_example, save_history


def submit_feedback(
    run_id: str,
    style_score: int,
    character_score: int,
    motion_score: int,
    atmosphere_score: int,
    notes: str = "",
    video_path: str = "",
) -> ProductionPack:
    data = load_history(run_id)
    avg = (style_score + character_score + motion_score + atmosphere_score) / 4
    is_gold = avg >= 4 and min(style_score, character_score, motion_score, atmosphere_score) >= 3
    fb = Feedback(
        style_score=style_score,
        character_score=character_score,
        motion_score=motion_score,
        atmosphere_score=atmosphere_score,
        notes=notes.strip(),
        video_path=video_path.strip(),
        is_gold=is_gold,
    )
    data["feedback"] = fb.model_dump()
    save_history(data)
    if is_gold:
        save_gold_example(data, "gold")
    return ProductionPack.model_validate(data)
