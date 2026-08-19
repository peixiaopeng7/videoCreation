# 聊斋短片工作室（本地 v0.1）

个人用本地工具：把短文压成 **6–15 秒**可拍包，导出 Midjourney / 即梦 Seedance 提示词，并对成片打分回流。

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 可选：填 LLM_API_KEY
python app.py
```

浏览器打开：http://127.0.0.1:7860

未配置 `LLM_API_KEY` 时走本地模板，仍可完整跑通：生成 → 复制提示词 → 打分。

## 工作流

1. 贴短文 / 梗 → 选风格包与时长档（8s / 12s / 15s）
2. 复制 MJ 提示词 → Midjourney 定妆
3. 按镜复制 Seedance 提示词 → 即梦出短片
4. 历史页打四维分；高分自动进金样例，供下次 LLM 参考

## 目录

```
app.py                 Gradio 入口
src/                   生成管线、存储、反馈
data/style_packs/      风格包（可改 JSON 持续迭代）
data/history/          每次生成记录
data/gold/             高分金样例
```

## LLM（可选）

任意 OpenAI 兼容接口均可：

```env
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

DeepSeek / 通义 / SiliconFlow 等改 `LLM_BASE_URL` + `LLM_MODEL` 即可。
