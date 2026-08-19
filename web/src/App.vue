<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api } from './api'
import PromptBox from './components/PromptBox.vue'
import ScorePanel from './components/ScorePanel.vue'

const tab = ref('generate')
const llmStatus = ref('检测中…')
const stylePacks = ref([])
const sourceText = ref('')
const stylePackId = ref('guofeng-liaozhai-v0.1')
const duration = ref('12s')
const forceTemplate = ref(false)
const loading = ref(false)
const error = ref('')
const pack = ref(null)

const history = ref([])
const selectedHistoryId = ref('')
const historyLoading = ref(false)

const mjBundle = computed(() => pack.value?.mj_prompts_bundle || '')
const seedanceBundle = computed(() => pack.value?.seedance_prompts_bundle || '')

async function refreshMeta() {
  const [health, packs, hist] = await Promise.all([
    api.health(),
    api.stylePacks(),
    api.history(),
  ])
  llmStatus.value = health.llm
  stylePacks.value = packs
  if (packs.length && !packs.find((p) => p.id === stylePackId.value)) {
    stylePackId.value = packs[0].id
  }
  history.value = hist
}

async function generate() {
  error.value = ''
  if (!sourceText.value.trim()) {
    error.value = '请先贴一段短文或故事梗。'
    return
  }
  loading.value = true
  try {
    pack.value = await api.generate({
      source_text: sourceText.value.trim(),
      style_pack_id: stylePackId.value,
      duration_preset: duration.value,
      force_template: forceTemplate.value,
    })
    await refreshMeta()
    selectedHistoryId.value = pack.value.id
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

async function loadHistory(id) {
  if (!id) return
  historyLoading.value = true
  error.value = ''
  try {
    pack.value = await api.historyDetail(id)
    selectedHistoryId.value = id
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    historyLoading.value = false
  }
}

async function onFeedbackSaved(updated) {
  pack.value = updated
  await refreshMeta()
}

watch(tab, (v) => {
  if (v === 'history') refreshMeta()
})

onMounted(() => {
  refreshMeta().catch((e) => {
    error.value = `后端连不上：${e.message}。请先在项目根目录运行 python server.py`
  })
})
</script>

<template>
  <div class="shell">
    <header class="top">
      <div>
        <p class="eyebrow">本地工作室 · Vue + FastAPI</p>
        <h1>聊斋短片</h1>
      </div>
      <p class="llm">{{ llmStatus }}</p>
    </header>

    <nav class="tabs">
      <button :class="{ active: tab === 'generate' }" @click="tab = 'generate'">生成</button>
      <button :class="{ active: tab === 'history' }" @click="tab = 'history'">历史与打分</button>
      <button :class="{ active: tab === 'help' }" @click="tab = 'help'">说明</button>
    </nav>

    <p v-if="error" class="error">{{ error }}</p>

    <section v-show="tab === 'generate'" class="panel">
      <div class="grid">
        <div class="col">
          <label class="field">
            <span>短文 / 故事梗</span>
            <textarea
              v-model="sourceText"
              rows="12"
              placeholder="贴一段聊斋改编梗、原文摘录或你自己的点子……"
            />
          </label>

          <label class="field">
            <span>风格包</span>
            <select v-model="stylePackId">
              <option v-for="p in stylePacks" :key="p.id" :value="p.id">
                {{ p.name }}（{{ p.id }}）
              </option>
            </select>
          </label>

          <div class="field">
            <span>时长档</span>
            <div class="seg">
              <button
                v-for="d in ['8s', '12s', '15s']"
                :key="d"
                type="button"
                :class="{ on: duration === d }"
                @click="duration = d"
              >
                {{ d }}
              </button>
            </div>
            <small>8s 单镜 / 12s 两镜 / 15s 三镜</small>
          </div>

          <label class="check">
            <input v-model="forceTemplate" type="checkbox" />
            强制本地模板（不调大模型）
          </label>

          <button class="primary" :disabled="loading" @click="generate">
            {{ loading ? '生成中…' : '生成可拍包' }}
          </button>
        </div>

        <div class="col">
          <article v-if="pack" class="result">
            <h2>{{ pack.script?.title }}</h2>
            <ul class="meta">
              <li>Run ID：<code>{{ pack.id }}</code></li>
              <li v-if="pack.mode">模式：{{ pack.mode }}</li>
              <li>时长：{{ pack.duration_preset }}（约 {{ pack.script?.duration_sec }} 秒）</li>
            </ul>
            <p><strong>Logline</strong> {{ pack.script?.logline }}</p>
            <p><strong>冲突</strong> {{ pack.script?.conflict }}</p>
            <pre class="script">{{ pack.script?.full_script }}</pre>

            <h3>角色</h3>
            <ul>
              <li v-for="c in pack.characters" :key="c.id">
                <strong>{{ c.name }}</strong>（{{ c.role }}）— {{ c.appearance }} / {{ c.costume }} / {{ c.makeup }}
              </li>
            </ul>

            <h3>分镜</h3>
            <ol>
              <li v-for="s in pack.shots" :key="s.index">
                <strong>{{ s.shot_type }}</strong>（{{ s.duration_sec }}s）— {{ s.action }}
                <span v-if="s.dialogue">｜「{{ s.dialogue }}」</span>
              </li>
            </ol>
          </article>
          <div v-else class="empty">生成结果会出现在这里</div>
        </div>
      </div>

      <div v-if="pack" class="prompts">
        <PromptBox title="Midjourney 角色提示词" :text="mjBundle" />
        <PromptBox title="即梦 Seedance 分镜提示词" :text="seedanceBundle" />
      </div>
    </section>

    <section v-show="tab === 'history'" class="panel">
      <div class="hist-bar">
        <select v-model="selectedHistoryId" @change="loadHistory(selectedHistoryId)">
          <option value="">选择历史记录</option>
          <option v-for="h in history" :key="h.id" :value="h.id">
            {{ h.title }} · {{ h.id }}{{ h.is_gold ? ' ★' : '' }}
          </option>
        </select>
        <button class="ghost" @click="refreshMeta">刷新</button>
        <button
          class="ghost"
          :disabled="!selectedHistoryId || historyLoading"
          @click="loadHistory(selectedHistoryId)"
        >
          {{ historyLoading ? '加载中…' : '加载' }}
        </button>
      </div>

      <div v-if="pack" class="grid">
        <div class="col">
          <article class="result">
            <h2>{{ pack.script?.title }}</h2>
            <p>{{ pack.script?.logline }}</p>
            <PromptBox title="MJ" :text="mjBundle" />
            <PromptBox title="Seedance" :text="seedanceBundle" />
          </article>
        </div>
        <div class="col">
          <ScorePanel :run-id="pack.id" :existing="pack.feedback" @saved="onFeedbackSaved" />
        </div>
      </div>
      <div v-else class="empty">从上方选择一条历史，对着成片打分</div>
    </section>

    <section v-show="tab === 'help'" class="panel help">
      <h2>怎么用</h2>
      <ol>
        <li>生成页贴短文 → 出剧本与提示词</li>
        <li>复制 MJ 提示词去 Midjourney 定妆</li>
        <li>按镜复制 Seedance 提示词去即梦出 6–15 秒片</li>
        <li>历史页打四维分；高分进金样例，下次生成更稳</li>
      </ol>
      <h2>关于「大模型」是什么意思</h2>
      <p>
        把短文改成剧本，可以有两种方式：
      </p>
      <ul>
        <li><strong>本地模板</strong>：不联网、不花钱，用写死的结构先跑通流程（默认就能用）。</li>
        <li><strong>接大模型 API</strong>：像 ChatGPT / DeepSeek 那种，在 <code>.env</code> 里填密钥后，剧本会按你的原文真正改编，而不只是套模板。</li>
      </ul>
      <p>你现在可以先不管密钥，勾选「强制本地模板」或直接生成即可。</p>
    </section>
  </div>
</template>

<style scoped lang="scss">
.shell {
  max-width: 1180px;
  margin: 0 auto;
  padding: 28px 20px 64px;
}

.top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: end;
  margin-bottom: 18px;
}

.eyebrow {
  margin: 0 0 4px;
  color: var(--muted);
  font-size: 13px;
  letter-spacing: 0.08em;
}

h1 {
  margin: 0;
  font-family: var(--font-serif);
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.llm {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  max-width: 420px;
  text-align: right;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
}

.tabs button {
  border: 1px solid var(--line);
  background: transparent;
  color: var(--muted);
  padding: 8px 14px;
  border-radius: 999px;
}

.tabs button.active {
  color: var(--bg);
  background: var(--accent);
  border-color: var(--accent);
}

.error {
  background: color-mix(in srgb, var(--danger) 18%, transparent);
  border: 1px solid color-mix(in srgb, var(--danger) 45%, transparent);
  color: #ffd4cc;
  padding: 10px 12px;
  border-radius: var(--radius);
}

.panel {
  background: color-mix(in srgb, var(--bg-elev) 88%, transparent);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 18px;
  backdrop-filter: blur(8px);
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
  .llm {
    text-align: left;
  }
}

.col {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field span {
  color: var(--muted);
  font-size: 13px;
}

textarea,
select,
input[type='text'] {
  width: 100%;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 10px 12px;
}

textarea {
  resize: vertical;
  line-height: 1.6;
}

.seg {
  display: flex;
  gap: 8px;
}

.seg button {
  flex: 1;
  border: 1px solid var(--line);
  background: var(--bg-soft);
  border-radius: 8px;
  padding: 8px;
  color: var(--muted);
}

.seg button.on {
  border-color: var(--accent);
  color: var(--accent);
}

small {
  color: var(--muted);
}

.check {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 14px;
}

.primary,
.ghost {
  border-radius: 10px;
  padding: 10px 14px;
  border: 1px solid var(--line);
}

.primary {
  background: var(--accent);
  color: #1a140a;
  border-color: var(--accent);
  font-weight: 700;
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ghost {
  background: transparent;
  color: var(--text);
}

.result {
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px;
}

.result h2 {
  margin: 0 0 8px;
  font-family: var(--font-serif);
  font-size: 22px;
}

.result h3 {
  margin: 16px 0 8px;
  font-size: 15px;
  color: var(--accent);
}

.meta {
  padding-left: 18px;
  color: var(--muted);
  font-size: 13px;
}

.script {
  white-space: pre-wrap;
  background: var(--bg);
  border-radius: 8px;
  padding: 10px;
  font-size: 13px;
  line-height: 1.6;
  overflow: auto;
}

.empty {
  color: var(--muted);
  border: 1px dashed var(--line);
  border-radius: 12px;
  padding: 28px;
  text-align: center;
}

.prompts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 16px;
}

@media (max-width: 900px) {
  .prompts {
    grid-template-columns: 1fr;
  }
}

.hist-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.hist-bar select {
  flex: 1;
}

.help h2 {
  font-family: var(--font-serif);
  font-size: 20px;
}

.help code {
  background: var(--bg);
  padding: 1px 6px;
  border-radius: 4px;
}
</style>
