# 聊斋短片工作室（本地 v0.2）

Vue 前端 + 薄 FastAPI 后端。把短文压成 **6–15 秒**可拍包，导出 Midjourney / 即梦 Seedance 提示词，并对成片打分回流。

## 环境要求

- **Node.js ≥ 18.18**（推荐 20 LTS）。Node 16 会直接报错（`styleText` / Vite 不支持）。
- Python 3.10+

用 `node -v` 查看版本。Windows 可用 [nvm-windows](https://github.com/coreybutler/nvm-windows) 安装：

```bash
nvm install 20
nvm use 20
```

## 开发启动（两个终端）

```bash
# 终端 1：后端
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 可选
python server.py
```

```bash
# 终端 2：前端
cd web
rm -rf node_modules package-lock.json   # 若刚从旧依赖升级，先清一次
npm install
npm run dev
```

打开：http://127.0.0.1:5173（Vite 会把 `/api` 代理到后端 `7860`）
## 仅后端托管打包前端

```bash
cd web && npm run build && cd ..
python server.py
```

然后打开：http://127.0.0.1:7860

## 工作流

1. 贴短文 → 选风格包与时长档
2. 复制 MJ 提示词 → Midjourney 定妆
3. 复制 Seedance 提示词 → 即梦出短片
4. 历史页打分；高分进金样例

## 关于「要不要填大模型密钥」

- **不填也能用**：走本地模板，先跑通复制提示词 → 出片 → 打分。
- **填了更好用**：短文会按你的内容真正改编成剧本（任意 OpenAI 兼容接口，如 DeepSeek）。

```env
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

## 目录

```
server.py              FastAPI 入口
src/                   生成管线 / 存储 / 反馈
web/                   Vue3 + Vite 前端
data/style_packs/      风格包
data/history/          生成历史
data/gold/             高分金样例
```
