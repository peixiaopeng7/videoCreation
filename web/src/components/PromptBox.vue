<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  text: { type: String, default: '' },
})

const copied = ref(false)

watch(
  () => props.text,
  () => {
    copied.value = false
  },
)

async function copy() {
  if (!props.text) return
  await navigator.clipboard.writeText(props.text)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 1500)
}
</script>

<template>
  <div class="box">
    <div class="head">
      <h3>{{ title }}</h3>
      <button type="button" @click="copy">{{ copied ? '已复制' : '复制' }}</button>
    </div>
    <textarea :value="text" readonly rows="10" />
  </div>
</template>

<style scoped>
.box {
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

h3 {
  margin: 0;
  font-size: 14px;
  color: var(--accent);
  font-weight: 600;
}

button {
  border: 1px solid var(--line);
  background: var(--bg);
  border-radius: 8px;
  padding: 4px 10px;
  font-size: 13px;
}

textarea {
  width: 100%;
  resize: vertical;
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px;
  line-height: 1.55;
  font-size: 13px;
}
</style>
