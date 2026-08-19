<script setup>
import { reactive, ref, watch } from 'vue'
import { api } from '../api'

const props = defineProps({
  runId: { type: String, required: true },
  existing: { type: Object, default: null },
})

const emit = defineEmits(['saved'])

const form = reactive({
  style_score: 3,
  character_score: 3,
  motion_score: 3,
  atmosphere_score: 3,
  notes: '',
  video_path: '',
})
const saving = ref(false)
const message = ref('')
const error = ref('')

watch(
  () => props.existing,
  (v) => {
    if (!v) return
    form.style_score = v.style_score ?? 3
    form.character_score = v.character_score ?? 3
    form.motion_score = v.motion_score ?? 3
    form.atmosphere_score = v.atmosphere_score ?? 3
    form.notes = v.notes || ''
    form.video_path = v.video_path || ''
  },
  { immediate: true },
)

async function submit() {
  saving.value = true
  error.value = ''
  message.value = ''
  try {
    const updated = await api.feedback({
      run_id: props.runId,
      ...form,
    })
    const gold = updated.feedback?.is_gold
    message.value = gold
      ? '已保存，并入库为金样例。'
      : '反馈已保存。'
    emit('saved', updated)
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="score">
    <h3>对着成片打分</h3>
    <label v-for="item in [
      ['style_score', '风格像不像'],
      ['character_score', '角色稳不稳'],
      ['motion_score', '动作/镜头清不清'],
      ['atmosphere_score', '志怪味'],
    ]" :key="item[0]" class="row">
      <span>{{ item[1] }} · {{ form[item[0]] }}</span>
      <input v-model.number="form[item[0]]" type="range" min="1" max="5" step="1" />
    </label>

    <label class="field">
      <span>成片路径/链接（可选）</span>
      <input v-model="form.video_path" type="text" placeholder="/path/to/clip.mp4" />
    </label>
    <label class="field">
      <span>短评</span>
      <textarea v-model="form.notes" rows="4" placeholder="哪里不像、哪句提示词有用…" />
    </label>

    <button class="primary" :disabled="saving" @click="submit">
      {{ saving ? '提交中…' : '提交反馈' }}
    </button>
    <p v-if="message" class="ok">{{ message }}</p>
    <p v-if="error" class="err">{{ error }}</p>
  </div>
</template>

<style scoped>
.score {
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

h3 {
  margin: 0;
  font-family: var(--font-serif);
}

.row,
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.row span,
.field span {
  color: var(--muted);
  font-size: 13px;
}

input[type='range'] {
  width: 100%;
}

input[type='text'],
textarea {
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 8px 10px;
}

.primary {
  background: var(--accent);
  color: #1a140a;
  border: none;
  border-radius: 10px;
  padding: 10px 14px;
  font-weight: 700;
}

.ok {
  color: var(--ok);
  margin: 0;
}

.err {
  color: var(--danger);
  margin: 0;
}
</style>
