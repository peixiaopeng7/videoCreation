from __future__ import annotations

import json
from pathlib import Path

import gradio as gr

from src.feedback import submit_feedback
from src.llm import LLMConfig
from src.pipeline import generate_production_pack
from src.storage import list_history, list_style_packs, load_history

ROOT = Path(__file__).resolve().parent


def _style_choices() -> list[str]:
    packs = list_style_packs()
    return [f"{p.id} | {p.name}" for p in packs]


def _parse_style_choice(choice: str) -> str:
    return choice.split("|", 1)[0].strip()


def _history_choices() -> list[str]:
    items = list_history(80)
    out = []
    for it in items:
        title = (it.get("script") or {}).get("title", "未命名")
        out.append(f"{it['id']} | {title}")
    return out


def _parse_history_choice(choice: str) -> str:
    return choice.split("|", 1)[0].strip()


def _format_pack_markdown(pack_dict: dict, mode: str = "") -> str:
    script = pack_dict.get("script") or {}
    chars = pack_dict.get("characters") or []
    shots = pack_dict.get("shots") or []
    fb = pack_dict.get("feedback")
    lines = [
        f"### {script.get('title', '未命名')}",
        f"- **Run ID**: `{pack_dict.get('id')}`",
        f"- **风格包**: `{pack_dict.get('style_pack_id')}`",
        f"- **时长档**: `{pack_dict.get('duration_preset')}`（约 {script.get('duration_sec')} 秒）",
    ]
    if mode:
        lines.append(f"- **生成模式**: {mode}")
    lines.extend(
        [
            "",
            f"**Logline**：{script.get('logline', '')}",
            f"**冲突**：{script.get('conflict', '')}",
            f"**收束**：{script.get('ending_tone', '')}",
            "",
            "#### 短剧本",
            f"```\n{script.get('full_script', '')}\n```",
            "",
            "#### 角色",
        ]
    )
    for c in chars:
        lines.append(
            f"- **{c.get('name')}**（{c.get('role')}）：{c.get('appearance')} / "
            f"{c.get('costume')} / {c.get('makeup')}"
        )
    lines.append("")
    lines.append("#### 分镜")
    for s in shots:
        lines.append(
            f"{s.get('index')}. **{s.get('shot_type')}** ({s.get('duration_sec')}s) — "
            f"{s.get('action')}｜对白：{s.get('dialogue') or '（无）'}"
        )
    if fb:
        lines.extend(
            [
                "",
                "#### 已有反馈",
                f"- 风格 {fb.get('style_score')} / 角色 {fb.get('character_score')} / "
                f"镜头 {fb.get('motion_score')} / 志怪味 {fb.get('atmosphere_score')}",
                f"- 金样例：{'是' if fb.get('is_gold') else '否'}",
                f"- 备注：{fb.get('notes') or '（无）'}",
            ]
        )
    return "\n".join(lines)


def ui_generate(source_text: str, style_choice: str, duration: str, force_template: bool):
    if not source_text or not source_text.strip():
        raise gr.Error("请先贴一段短文或故事梗。")
    if not style_choice:
        raise gr.Error("请选择风格包。")
    pack, mode = generate_production_pack(
        source_text=source_text.strip(),
        style_pack_id=_parse_style_choice(style_choice),
        duration_preset=duration,  # type: ignore[arg-type]
        force_template=force_template,
    )
    data = pack.model_dump()
    md = _format_pack_markdown(data, mode=mode)
    hist_label = f"{pack.id} | {pack.script.title}"
    return (
        md,
        pack.mj_prompts_bundle,
        pack.seedance_prompts_bundle,
        pack.id,
        json.dumps(data, ensure_ascii=False, indent=2),
        gr.update(choices=_history_choices(), value=hist_label),
    )


def ui_load_history(choice: str):
    if not choice:
        raise gr.Error("请选择一条历史记录。")
    data = load_history(_parse_history_choice(choice))
    mj = data.get("mj_prompts_bundle") or "\n\n".join(
        f"【{c.get('name')}】\n{c.get('mj_prompt')}" for c in data.get("characters") or []
    )
    seedance = data.get("seedance_prompts_bundle") or "\n\n".join(
        f"【镜{s.get('index')}】\n{s.get('seedance_prompt')}" for s in data.get("shots") or []
    )
    return (
        _format_pack_markdown(data),
        mj,
        seedance,
        data.get("id", ""),
        json.dumps(data, ensure_ascii=False, indent=2),
    )


def ui_feedback(
    run_id: str,
    style_score: int,
    character_score: int,
    motion_score: int,
    atmosphere_score: int,
    notes: str,
    video_path: str,
):
    if not run_id or not run_id.strip():
        raise gr.Error("没有 Run ID。请先生成或从历史加载。")
    pack = submit_feedback(
        run_id=run_id.strip(),
        style_score=int(style_score),
        character_score=int(character_score),
        motion_score=int(motion_score),
        atmosphere_score=int(atmosphere_score),
        notes=notes or "",
        video_path=video_path or "",
    )
    gold = (
        "已入库为金样例，下次生成会优先参考。"
        if pack.feedback and pack.feedback.is_gold
        else "已保存反馈。"
    )
    return f"反馈已写入 `{pack.id}`。{gold}", _format_pack_markdown(pack.model_dump())


def build_app() -> gr.Blocks:
    llm = LLMConfig()
    style_opts = _style_choices()
    default_style = style_opts[0] if style_opts else None

    with gr.Blocks(title="聊斋短片工作室") as demo:
        gr.Markdown(
            f"""
# 聊斋短片工作室（本地 v0.1）

短文 → 可拍短剧本 → Midjourney 角色提示词 → 即梦 Seedance 分镜提示词 → 成片打分回流。

**LLM 状态**：{llm.status_text()}  
在项目根目录复制 `.env.example` 为 `.env` 可接入 OpenAI 兼容接口。
"""
        )

        with gr.Tab("生成"):
            with gr.Row():
                with gr.Column(scale=1):
                    source = gr.Textbox(
                        label="短文 / 故事梗",
                        lines=10,
                        placeholder="贴一段聊斋改编梗、原文摘录或你自己的故事点子……",
                    )
                    style = gr.Dropdown(
                        label="风格包",
                        choices=style_opts,
                        value=default_style,
                    )
                    duration = gr.Radio(
                        label="时长档",
                        choices=["8s", "12s", "15s"],
                        value="12s",
                        info="8s 单镜 / 12s 两镜 / 15s 三镜",
                    )
                    force_template = gr.Checkbox(
                        label="强制使用本地模板（忽略 LLM）",
                        value=False,
                    )
                    gen_btn = gr.Button("生成可拍包", variant="primary")
                with gr.Column(scale=1):
                    overview = gr.Markdown()
                    run_id = gr.Textbox(label="Run ID", interactive=False)

            with gr.Row():
                mj_out = gr.Textbox(label="Midjourney 角色提示词（复制到 MJ）", lines=12)
                seedance_out = gr.Textbox(label="即梦 Seedance 分镜提示词（按镜复制）", lines=12)

            raw_json = gr.Code(label="完整 JSON（可备份）", language="json")

        with gr.Tab("历史与打分"):
            with gr.Row():
                history_dd = gr.Dropdown(label="历史记录", choices=_history_choices())
                refresh_btn = gr.Button("刷新列表")
                load_btn = gr.Button("加载")
            hist_overview = gr.Markdown()
            with gr.Row():
                hist_mj = gr.Textbox(label="MJ 提示词", lines=8)
                hist_seedance = gr.Textbox(label="Seedance 提示词", lines=8)
            hist_run_id = gr.Textbox(label="当前 Run ID", interactive=False)
            hist_json = gr.Code(label="JSON", language="json")

            gr.Markdown("### 对着成片打分（1–5）")
            with gr.Row():
                s_style = gr.Slider(1, 5, value=3, step=1, label="风格像不像")
                s_char = gr.Slider(1, 5, value=3, step=1, label="角色稳不稳")
                s_motion = gr.Slider(1, 5, value=3, step=1, label="动作/镜头清不清")
                s_atm = gr.Slider(1, 5, value=3, step=1, label="志怪味")
            video_path = gr.Textbox(label="成片本地路径或链接（可选）")
            notes = gr.Textbox(label="短评（哪里不像、哪句提示词有用）", lines=3)
            fb_btn = gr.Button("提交反馈", variant="primary")
            fb_msg = gr.Markdown()

            refresh_btn.click(
                lambda: gr.update(choices=_history_choices()),
                outputs=[history_dd],
            )
            load_btn.click(
                ui_load_history,
                inputs=[history_dd],
                outputs=[hist_overview, hist_mj, hist_seedance, hist_run_id, hist_json],
            )
            fb_btn.click(
                ui_feedback,
                inputs=[hist_run_id, s_style, s_char, s_motion, s_atm, notes, video_path],
                outputs=[fb_msg, hist_overview],
            )

        with gr.Tab("使用说明"):
            gr.Markdown(
                """
## 推荐工作流

1. **生成**页贴短文，选 `12s` 或 `15s`，点生成。
2. 复制 **MJ 提示词** 去 Midjourney 出定妆；选中可用图后自行存档（下版可加定妆回填）。
3. 按镜复制 **Seedance 提示词** 到即梦；出 6–15 秒成片。
4. 回到 **历史与打分**，加载该 Run，打四维分并写短评。
5. 均分 ≥ 4 且单项 ≥ 3 会进入金样例库，下次 LLM 生成会检索参考。

## 环境变量

```bash
cp .env.example .env
# LLM_API_KEY=...
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_MODEL=gpt-4o-mini
```

未配置时会用本地模板，方便先跑通「复制提示词 → 出片 → 打分」闭环。
"""
            )

        gen_btn.click(
            ui_generate,
            inputs=[source, style, duration, force_template],
            outputs=[overview, mj_out, seedance_out, run_id, raw_json, history_dd],
        )

        # After generate, also mirror run_id into scoring tab for convenience
        def _sync_run_id(rid: str):
            return rid

        run_id.change(_sync_run_id, inputs=[run_id], outputs=[hist_run_id])

    return demo


def main() -> None:
    demo = build_app()
    demo.launch(server_name="127.0.0.1", server_port=7860, show_error=True)


if __name__ == "__main__":
    main()
