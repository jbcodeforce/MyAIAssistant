import { ref } from 'vue'
import { fetchNotesMarkdown } from '@/services/api'
import { renderMarkdownForNotesWithDocLinks } from '@/utils/markdownNotes'

/**
 * Modal state and click handler for organization note document links.
 */
export function useNotesDocLinkModal() {
  const showDocModal = ref(false)
  const docModalTitle = ref('')
  const docModalHtml = ref('')
  const docModalLoading = ref(false)
  const docModalError = ref('')

  let activeContextBase = ''

  function closeDocModal() {
    showDocModal.value = false
    docModalTitle.value = ''
    docModalHtml.value = ''
    docModalError.value = ''
    docModalLoading.value = false
  }

  async function openNotesDoc(relativePath, title, contextBase) {
    if (!relativePath || !contextBase) return
    activeContextBase = contextBase
    showDocModal.value = true
    docModalTitle.value = title || relativePath
    docModalHtml.value = ''
    docModalError.value = ''
    docModalLoading.value = true
    try {
      const raw = await fetchNotesMarkdown(contextBase, relativePath)
      docModalHtml.value = renderMarkdownForNotesWithDocLinks(raw, contextBase)
    } catch (err) {
      docModalError.value = err.message || 'Failed to load document'
    } finally {
      docModalLoading.value = false
    }
  }

  function onMarkdownClick(event, contextBase) {
    const anchor = event.target.closest?.('a.notes-doc-link')
    if (!anchor || !contextBase) return
    const relPath = anchor.getAttribute('data-notes-doc')
    if (!relPath) return
    event.preventDefault()
    event.stopPropagation()
    const label =
      anchor.getAttribute('data-notes-doc-label') ||
      (anchor.textContent || '').trim() ||
      relPath
    openNotesDoc(relPath, label, contextBase)
  }

  function onDocModalContentClick(event) {
    if (activeContextBase) {
      onMarkdownClick(event, activeContextBase)
    }
  }

  return {
    showDocModal,
    docModalTitle,
    docModalHtml,
    docModalLoading,
    docModalError,
    closeDocModal,
    openNotesDoc,
    onMarkdownClick,
    onDocModalContentClick
  }
}
