async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = { detail: text }
  }
  if (!res.ok) {
    const msg = data?.detail || data?.message || res.statusText
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  return data
}

export const api = {
  health: () => request('/api/health'),
  stylePacks: () => request('/api/style-packs'),
  generate: (body) =>
    request('/api/generate', { method: 'POST', body: JSON.stringify(body) }),
  history: () => request('/api/history'),
  historyDetail: (id) => request(`/api/history/${encodeURIComponent(id)}`),
  feedback: (body) =>
    request('/api/feedback', { method: 'POST', body: JSON.stringify(body) }),
}
