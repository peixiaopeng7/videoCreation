from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from .llm import LLMConfig, chat_json
from .models import (
    CharacterCard,
    DurationPresetId,
    ProductionPack,
    ShortScript,
    Shot,
    StylePack,
)
from .storage import load_gold_examples, load_style_pack, save_history


DURATION_SHOT_PLAN: dict[str, list[str]] = {
    "8s": ["reaction_closeup"],
    "12s": ["establishing_night_room", "two_shot_bed_talk"],
    "15s": ["establishing_night_room", "two_shot_bed_talk", "reaction_closeup"],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]


def _clip(text: str, n: int = 80) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return text if len(text) <= n else text[: n - 1] + "…"


def _preset_seconds(style: StylePack, preset: DurationPresetId) -> int:
    for item in style.duration_presets:
        if item.get("id") == preset:
            return int(item.get("seconds", 12))
    return {"8s": 8, "12s": 12, "15s": 15}[preset]


def _template_lookup(style: StylePack, template_id: str) -> dict:
    for t in style.shot_templates:
        if t.get("id") == template_id:
            return t
    return {"id": template_id, "name": template_id, "seedance_hint": ""}


def _gold_context() -> str:
    golds = load_gold_examples(limit=3)
    if not golds:
        return "（暂无金样例）"
    chunks = []
    for g in golds:
        script = g.get("script", {})
        fb = g.get("feedback") or {}
        chunks.append(
            f"- 标题:{script.get('title')} / logline:{script.get('logline')} / "
            f"评分风格{fb.get('style_score')}角色{fb.get('character_score')} "
            f"备注:{fb.get('notes', '')}"
        )
    return "\n".join(chunks)


def generate_with_llm(
    source_text: str,
    style: StylePack,
    duration_preset: DurationPresetId,
    cfg: LLMConfig,
) -> dict:
    seconds = _preset_seconds(style, duration_preset)
    shot_ids = DURATION_SHOT_PLAN[duration_preset]
    templates = [_template_lookup(style, sid) for sid in shot_ids]

    system = (
        "你是聊斋志异/中国古代志怪短片编剧与分镜提示词助手。"
        "输出必须是 JSON。目标是可拍的短视频（数秒到十几秒），不是长剧。"
        "对白文言白话夹杂但忌网络梗；气氛靠人情与异感，不靠跳吓。"
    )
    user = f"""
风格包：{style.name}（{style.id}）
美学要点：{json_dumps(style.aesthetic)}
禁止：{style.forbidden_notes}
金样例参考：
{_gold_context()}

用户短文/梗：
{source_text}

请生成总时长约 {seconds} 秒、镜头模板顺序为 {[t.get('name') for t in templates]} 的可拍包。
JSON schema:
{{
  "script": {{
    "title": str,
    "logline": str,
    "theme": str,
    "conflict": str,
    "ending_tone": str,
    "scenes_summary": str,
    "full_script": str
  }},
  "characters": [
    {{
      "name": str,
      "role": str,
      "gender": str,
      "appearance": str,
      "costume": str,
      "hair": str,
      "makeup": str,
      "personality": str
    }}
  ],
  "shots": [
    {{
      "template_id": str,  // 必须按顺序使用: {[t['id'] for t in templates]}
      "shot_type": str,
      "action": str,
      "dialogue": str,
      "emotion": str
    }}
  ]
}}
角色 1~2 个即可。shots 数量必须为 {len(templates)}。
"""
    return chat_json(system, user.strip(), cfg)


def json_dumps(obj: object) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False)


def generate_with_templates(
    source_text: str,
    style: StylePack,
    duration_preset: DurationPresetId,
) -> dict:
    """Offline fallback so the tool works before LLM keys are configured."""
    seconds = _preset_seconds(style, duration_preset)
    snippet = _clip(source_text, 40)
    title = f"夜话·{_clip(source_text, 12)}"
    conflict = "一夜相守之后，人却总要离去"
    logline = f"据「{snippet}」压缩：月下对坐，问别离。"

    characters = [
        {
            "name": "书生",
            "role": "生",
            "gender": "男",
            "appearance": "清瘦俊朗，神情克制",
            "costume": "月白层叠长衫，浅米色腰绦，外袍略透",
            "hair": "黑发顶髻，白金简簪",
            "makeup": "吊眉，眼尾丹红延伸至颞，冷峻",
            "personality": "寡言、心软却不愿承诺",
        },
        {
            "name": "狐女",
            "role": "旦",
            "gender": "女",
            "appearance": "容色明艳却带忧色",
            "costume": "青绿罗衣，袖上暗花，朱红领缘，内衬淡黄",
            "hair": "高髻，金簪与朱红饰",
            "makeup": "柔粉眼晕，眉峰入鬓，神情恳切",
            "personality": "温软追问，不甘只做一夜之缘",
        },
    ]

    shot_ids = DURATION_SHOT_PLAN[duration_preset]
    dialogue_map = {
        "establishing_night_room": "",
        "two_shot_bed_talk": "哪一次不是住一夜就走？",
        "reaction_closeup": "……今夜亦如是。",
    }
    action_map = {
        "establishing_night_room": "冷蓝夜室，窗棂外月色，纱帐轻晃，罗汉床隐约可见两人轮廓",
        "two_shot_bed_talk": "二人对坐床沿，狐女侧身追问，书生目光垂落不答",
        "reaction_closeup": "书生近景，眉眼紧绷，片刻后轻轻转开视线",
    }
    emotion_map = {
        "establishing_night_room": "清冷、期待",
        "two_shot_bed_talk": "哀婉、对峙",
        "reaction_closeup": "隐忍、逃离",
    }
    shots = []
    for tid in shot_ids:
        tpl = _template_lookup(style, tid)
        shots.append(
            {
                "template_id": tid,
                "shot_type": tpl.get("name", tid),
                "action": action_map.get(tid, tpl.get("seedance_hint", "")),
                "dialogue": dialogue_map.get(tid, ""),
                "emotion": emotion_map.get(tid, ""),
            }
        )

    full_script = (
        f"【标题】{title}\n"
        f"【时长】约 {seconds} 秒\n"
        f"【主线】{logline}\n"
        f"【冲突】{conflict}\n"
        f"【对白】「哪一次不是住一夜就走？」——「……今夜亦如是。」\n"
        f"【原文压缩】{snippet}\n"
        "【说明】当前为本地模板生成；配置 LLM_API_KEY 后会按原文深度改编。"
    )

    return {
        "script": {
            "title": title,
            "logline": logline,
            "theme": "聚散无常",
            "conflict": conflict,
            "ending_tone": "怅惘余韵",
            "scenes_summary": "夜室对坐一问一答",
            "full_script": full_script,
        },
        "characters": characters,
        "shots": shots,
    }


def build_mj_prompt(char: dict, style: StylePack) -> str:
    parts = [
        f"character design sheet of {char['name']}, {char.get('gender', '')} {char.get('role', '')}",
        char.get("appearance", ""),
        char.get("costume", ""),
        char.get("hair", ""),
        char.get("makeup", ""),
        "front view, clean background, consistent face",
        style.mj_style_lock,
    ]
    neg = ", ".join(style.negative_keywords[:8])
    prompt = ", ".join(p for p in parts if p)
    return f"{prompt} --no {neg}"


def build_seedance_prompt(
    shot: dict,
    chars: list[dict],
    style: StylePack,
    seconds: float,
) -> str:
    char_desc = "；".join(
        f"{c['name']}（{c.get('costume', '')}，{c.get('makeup', '')}）" for c in chars[:2]
    )
    tpl = shot.get("template_id", "")
    hint = ""
    for t in style.shot_templates:
        if t.get("id") == tpl:
            hint = t.get("seedance_hint", "")
            break
    dialogue = shot.get("dialogue") or ""
    dialogue_bit = f"对白：「{dialogue}」。" if dialogue else ""
    return (
        f"{style.seedance_style_lock}。"
        f"镜头：{shot.get('shot_type')}，约 {seconds:.0f} 秒。"
        f"人物：{char_desc}。"
        f"动作：{shot.get('action')}。"
        f"情绪：{shot.get('emotion')}。"
        f"{dialogue_bit}"
        f"运镜参考：{hint}。"
        "保持线稿与妆面稳定，避免闪烁与变形。"
    )


def assemble_pack(
    source_text: str,
    style_pack_id: str,
    duration_preset: DurationPresetId,
    raw: dict,
) -> ProductionPack:
    style = load_style_pack(style_pack_id)
    total = _preset_seconds(style, duration_preset)
    shot_ids = DURATION_SHOT_PLAN[duration_preset]
    per = total / max(len(shot_ids), 1)

    characters: list[CharacterCard] = []
    for i, c in enumerate(raw.get("characters") or [], start=1):
        cid = f"c{i}-{c.get('name', '角色')}"
        mj = build_mj_prompt(c, style)
        characters.append(
            CharacterCard(
                id=cid,
                name=c.get("name", f"角色{i}"),
                role=c.get("role", ""),
                gender=c.get("gender", ""),
                appearance=c.get("appearance", ""),
                costume=c.get("costume", ""),
                hair=c.get("hair", ""),
                makeup=c.get("makeup", ""),
                personality=c.get("personality", ""),
                mj_prompt=mj,
            )
        )

    char_dicts = [c.model_dump() for c in characters]
    shots: list[Shot] = []
    raw_shots = raw.get("shots") or []
    for i, tid in enumerate(shot_ids):
        s = raw_shots[i] if i < len(raw_shots) else {}
        merged = {
            "template_id": tid,
            "shot_type": s.get("shot_type") or _template_lookup(style, tid).get("name", tid),
            "action": s.get("action", ""),
            "dialogue": s.get("dialogue", ""),
            "emotion": s.get("emotion", ""),
        }
        prompt = build_seedance_prompt(merged, char_dicts, style, per)
        shots.append(
            Shot(
                index=i + 1,
                duration_sec=round(per, 1),
                template_id=tid,
                shot_type=merged["shot_type"],
                action=merged["action"],
                dialogue=merged["dialogue"],
                emotion=merged["emotion"],
                seedance_prompt=prompt,
                continuity_notes="沿用同一角色定妆图；色温冷蓝一致；线稿粗细稳定",
            )
        )

    script_raw = raw.get("script") or {}
    script = ShortScript(
        title=script_raw.get("title", "未命名短片"),
        logline=script_raw.get("logline", ""),
        duration_sec=total,
        theme=script_raw.get("theme", ""),
        conflict=script_raw.get("conflict", ""),
        ending_tone=script_raw.get("ending_tone", ""),
        scenes_summary=script_raw.get("scenes_summary", ""),
        full_script=script_raw.get("full_script", ""),
    )

    mj_bundle = "\n\n".join(
        f"【{c.name}】\n{c.mj_prompt}" for c in characters
    )
    seedance_bundle = "\n\n".join(
        f"【镜{s.index} · {s.shot_type} · {s.duration_sec}s】\n{s.seedance_prompt}"
        for s in shots
    )

    pack = ProductionPack(
        id=_new_id(),
        created_at=_now_iso(),
        source_text=source_text.strip(),
        style_pack_id=style_pack_id,
        duration_preset=duration_preset,
        script=script,
        characters=characters,
        shots=shots,
        mj_prompts_bundle=mj_bundle,
        seedance_prompts_bundle=seedance_bundle,
    )
    save_history(pack.model_dump())
    return pack


def generate_production_pack(
    source_text: str,
    style_pack_id: str,
    duration_preset: DurationPresetId = "12s",
    force_template: bool = False,
) -> tuple[ProductionPack, str]:
    style = load_style_pack(style_pack_id)
    cfg = LLMConfig()
    mode = "template"
    if force_template or not cfg.enabled:
        raw = generate_with_templates(source_text, style, duration_preset)
        mode = "template"
    else:
        try:
            raw = generate_with_llm(source_text, style, duration_preset, cfg)
            mode = "llm"
        except Exception as exc:  # noqa: BLE001 - fall back for local UX
            raw = generate_with_templates(source_text, style, duration_preset)
            mode = f"template(fallback after LLM error: {exc})"
    pack = assemble_pack(source_text, style_pack_id, duration_preset, raw)
    return pack, mode
