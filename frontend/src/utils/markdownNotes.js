/**
 * Helpers for markdown notes: insert at cursor and rewrite relative image src for in-app display.
 * Supports {width=600px} (or %, em, rem) on images for max-width.
 */
import { Marked } from 'marked'
import { getNotesFileUrl } from '@/services/api'

/** Sanitize organization name for path (match backend). */
export function sanitizeOrgNameForPath(name) {
  if (!name || typeof name !== 'string') return 'unknown'
  let s = name.toLowerCase().replace(/\s+/g, '-')
  s = s.replace(/[^a-z0-9\-_]/g, '').replace(/-+/g, '-').replace(/^-|-$/g, '')
  return s || 'unknown'
}

/** Context base for meeting note images from file_ref (e.g. "acme/proj/file.md" -> "meetings/acme/proj"). */
export function meetingNotesContextBaseFromFileRef(fileRef) {
  if (!fileRef || typeof fileRef !== 'string') return ''
  const trimmed = fileRef.trim()
  const dir = trimmed.includes('/') ? trimmed.replace(/\/[^/]+$/, '') : '.'
  return dir === '.' ? 'meetings' : `meetings/${dir}`
}

/**
 * Insert text at the current cursor position in a textarea and update the bound value.
 * @param {HTMLTextAreaElement} el - The textarea element
 * @param {string} text - Text to insert (e.g. '![](./images/name.png)')
 * @param {function(string): void} setValue - Callback to set the new full value (for v-model)
 */
export function insertMarkdownAtCursor(el, text, setValue) {
  if (!el || !setValue) return
  const start = el.selectionStart
  const end = el.selectionEnd
  const value = el.value ?? ''
  const newValue = value.slice(0, start) + text + value.slice(end)
  setValue(newValue)
  const newPos = start + text.length
  el.focus()
  el.setSelectionRange(newPos, newPos)
}

/**
 * Preprocess markdown: convert ](url){width=600px} to ](url "data-width:600px") so the image
 * renderer can add style="max-width:600px". Supports px, %, em, rem.
 */
function preprocessImageWidths(md) {
  if (!md || typeof md !== 'string') return md || ''
  return md.replace(/\)\s*\{width=([^}]+)\}/g, ' "data-width:$1")')
}

/** Allow only safe CSS width values (number + px|%|em|rem). */
function sanitizeWidth(value) {
  if (!value || typeof value !== 'string') return ''
  const m = value.trim().match(/^(\d+(?:\.\d+)?)\s*(px|%|em|rem)$/i)
  return m ? `${m[1]}${m[2].toLowerCase()}` : ''
}

/** Create a Marked instance with image renderer that applies data-width as max-width. */
function createNotesMarked() {
  return new Marked({
    renderer: {
      image({ href, title, text }) {
        const escapedHref = (href || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        const escapedAlt = (text || '').replace(/"/g, '&quot;')
        let style = ''
        if (title && title.startsWith('data-width:')) {
          const w = sanitizeWidth(title.slice('data-width:'.length))
          if (w) style = ` style="max-width:${w}"`
        }
        const titleAttr = (title && !title.startsWith('data-width:')) ? ` title="${String(title).replace(/"/g, '&quot;')}"` : ''
        return `<img src="${escapedHref}" alt="${escapedAlt}"${titleAttr}${style}>`
      }
    }
  })
}

let _notesMarked = null
function getNotesMarked() {
  if (!_notesMarked) _notesMarked = createNotesMarked()
  return _notesMarked
}

/**
 * Parse note markdown with image width support and return HTML. Does not rewrite image URLs
 * (use renderMarkdownForNotes for full pipeline including notes-files URL rewrite).
 */
export function parseNoteMarkdown(md) {
  if (!md || typeof md !== 'string') return ''
  const processed = preprocessImageWidths(md)
  return getNotesMarked().parse(processed)
}

/**
 * Full pipeline: preprocess {width=...}, parse markdown with custom image renderer, then
 * rewrite relative img src to notes-files API URLs.
 * @param {string} content - Raw markdown
 * @param {string} contextBase - Base path for serve API (e.g. 'meetings/acme/proj' or 'my-org')
 */
export function renderMarkdownForNotes(content, contextBase) {
  const html = parseNoteMarkdown(content || '')
  return renderMarkdownWithNoteImages(html, contextBase)
}

/**
 * Rewrite HTML from marked() so that img src starting with ./ use the notes-files API.
 * @param {string} html - Raw HTML from marked(markdown)
 * @param {string} contextBase - Base path for serve API (e.g. 'meetings/acme/proj' or 'my-org')
 * @returns {string} HTML with relative image src replaced by /api/notes-files/... URLs
 */
export function renderMarkdownWithNoteImages(html, contextBase) {
  if (!html || typeof html !== 'string') return html || ''
  if (!contextBase) return html
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')
  const imgs = doc.querySelectorAll('img[src^="./"]')
  imgs.forEach((img) => {
    const src = img.getAttribute('src')
    if (src) {
      img.setAttribute('src', getNotesFileUrl(contextBase, src))
    }
  })
  return doc.body?.innerHTML ?? html
}
