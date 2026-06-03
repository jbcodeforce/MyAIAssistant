/** Normalize meeting past/next steps from API or form state. */

export function normalizeStepsFromApi(steps) {
  if (!Array.isArray(steps)) return []
  return steps.map((s) => ({
    what: s.what || '',
    who: s.who || '',
    todo_id: s.todo_id ?? null
  }))
}

export function normalizeStepsForPayload(steps) {
  if (!Array.isArray(steps)) return null
  const out = steps
    .filter((s) => s.what && String(s.what).trim())
    .map((s) => {
      const row = {
        what: String(s.what).trim(),
        who: (s.who && String(s.who).trim()) || ''
      }
      if (s.todo_id != null) row.todo_id = s.todo_id
      return row
    })
  return out.length ? out : null
}
