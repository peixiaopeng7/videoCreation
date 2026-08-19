from __future__ import annotations

import json
from pathlib import Path

from .models import StylePack

ROOT = Path(__file__).resolve().parents[1]
STYLE_DIR = ROOT / "data" / "style_packs"
HISTORY_DIR = ROOT / "data" / "history"
GOLD_DIR = ROOT / "data" / "gold"


def ensure_dirs() -> None:
    STYLE_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)


def list_style_packs() -> list[StylePack]:
    ensure_dirs()
    packs: list[StylePack] = []
    for path in sorted(STYLE_DIR.glob("*.json")):
        packs.append(StylePack.model_validate_json(path.read_text(encoding="utf-8")))
    return packs


def load_style_pack(pack_id: str) -> StylePack:
    path = STYLE_DIR / f"{pack_id}.json"
    if not path.exists():
        # allow filename without assuming id==filename
        for p in STYLE_DIR.glob("*.json"):
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("id") == pack_id:
                return StylePack.model_validate(data)
        raise FileNotFoundError(f"风格包不存在: {pack_id}")
    return StylePack.model_validate_json(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_history(limit: int = 50) -> list[dict]:
    ensure_dirs()
    files = sorted(HISTORY_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    items: list[dict] = []
    for path in files[:limit]:
        items.append(json.loads(path.read_text(encoding="utf-8")))
    return items


def load_history(pack_run_id: str) -> dict:
    path = HISTORY_DIR / f"{pack_run_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"历史记录不存在: {pack_run_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_history(data: dict) -> Path:
    ensure_dirs()
    path = HISTORY_DIR / f"{data['id']}.json"
    save_json(path, data)
    return path


def save_gold_example(data: dict, tag: str) -> Path:
    ensure_dirs()
    path = GOLD_DIR / f"{data['id']}_{tag}.json"
    save_json(path, data)
    return path


def load_gold_examples(limit: int = 10) -> list[dict]:
    ensure_dirs()
    files = sorted(GOLD_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [json.loads(p.read_text(encoding="utf-8")) for p in files[:limit]]
