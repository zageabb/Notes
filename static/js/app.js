(() => {
  const shell = document.getElementById('appShell');
  if (!shell) return;

  const qs = (s) => document.querySelector(s);
  const qsa = (s) => [...document.querySelectorAll(s)];
  const state = {
    noteId: shell.dataset.selectedId ? Number(shell.dataset.selectedId) : null,
    note: null,
    view: 'all',
    notebook: '',
    proposal: null,
    preview: false,
    saveTimer: null,
  };

  const api = async (url, options = {}) => {
    const headers = options.body instanceof FormData ? {} : {'Content-Type': 'application/json'};
    const response = await fetch(url, {...options, headers: {...headers, ...(options.headers || {})}});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || `${response.status} ${response.statusText}`);
    return data;
  };

  const escapeHtml = (value='') => value.replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
  const setSaveState = (text) => { qs('#saveState').textContent = text; };

  const renderAttachments = () => {
    const host = qs('#attachmentList');
    host.innerHTML = '';
    if (!state.note) return;
    if (state.note.legacy_image) {
      const legacy = document.createElement('div');
      legacy.className = 'attachment-chip';
      legacy.innerHTML = `<a href="/static/images/${encodeURIComponent(state.note.legacy_image)}" target="_blank" rel="noopener">Legacy image: ${escapeHtml(state.note.legacy_image)}</a>`;
      host.appendChild(legacy);
    }
    for (const a of state.note.attachments || []) {
      const chip = document.createElement('div');
      chip.className = 'attachment-chip';
      chip.innerHTML = `<a href="/attachments/${a.id}" target="_blank" rel="noopener">${escapeHtml(a.name)}</a>${a.has_text ? '<span title="Searchable text extracted">⌕</span>' : ''}<button data-delete-attachment="${a.id}" title="Remove">×</button>`;
      host.appendChild(chip);
    }
  };

  const populateNote = (note) => {
    state.note = note;
    state.noteId = note.id;
    qs('#editorEmpty').hidden = true;
    qs('#editorContent').hidden = false;
    qs('#titleInput').value = note.title || '';
    qs('#contentInput').value = note.content || '';
    qs('#tagsInput').value = (note.tags || []).join(', ');
    qs('#sourceUrlInput').value = note.source_url || '';
    qs('#notebookSelect').value = note.notebook_id || '';
    qs('#pinButton').classList.toggle('active', !!note.pinned);
    qs('#favouriteButton').classList.toggle('active', !!note.favourite);
    qs('#favouriteButton').textContent = note.favourite ? '★' : '☆';
    qs('#archiveButton').textContent = note.archived ? 'Unarchive' : 'Archive';
    qs('#trashButton').textContent = note.deleted ? 'Restore' : 'Trash';
    renderAttachments();
    qsa('.note-list-item').forEach(el => el.classList.toggle('selected', Number(el.dataset.noteId) === note.id));
    if (state.preview) renderPreview();
  };

  const selectNote = async (id) => {
    try {
      const note = await api(`/api/notes/${id}`);
      populateNote(note);
    } catch (err) {
      setSaveState(err.message);
    }
  };

  const refreshList = async () => {
    const params = new URLSearchParams({q: qs('#searchInput').value, view: state.view});
    if (state.notebook) params.set('notebook', state.notebook);
    const notes = await api(`/api/search?${params}`);
    const host = qs('#noteList');
    qs('#noteCount').textContent = notes.length;
    host.innerHTML = notes.length ? '' : '<div class="empty-state">No matching notes.</div>';
    for (const note of notes) {
      const button = document.createElement('button');
      button.className = `note-list-item ${note.id === state.noteId ? 'selected' : ''}`;
      button.dataset.noteId = note.id;
      button.innerHTML = `<div class="note-list-title">${note.pinned ? '📌 ' : ''}${escapeHtml(note.title)}</div><div class="note-list-meta">${escapeHtml(note.notebook || 'Inbox')} · ${note.updated_at ? new Date(note.updated_at).toLocaleString([], {day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit'}) : ''}</div><div class="note-list-preview">${escapeHtml(note.preview || '')}</div>`;
      host.appendChild(button);
    }
  };

  const saveNote = async () => {
    if (!state.noteId || !state.note) return;
    setSaveState('Saving…');
    const payload = {
      title: qs('#titleInput').value,
      content: qs('#contentInput').value,
      notebook_id: Number(qs('#notebookSelect').value),
      tags: qs('#tagsInput').value.split(',').map(x => x.trim()).filter(Boolean),
      source_url: qs('#sourceUrlInput').value,
    };
    try {
      const note = await api(`/api/notes/${state.noteId}`, {method:'PATCH', body: JSON.stringify(payload)});
      state.note = note;
      setSaveState(`Saved ${new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}`);
      await refreshList();
    } catch (err) {
      setSaveState(`Save failed: ${err.message}`);
    }
  };

  const scheduleSave = () => {
    setSaveState('Unsaved changes');
    clearTimeout(state.saveTimer);
    state.saveTimer = setTimeout(saveNote, 900);
  };

  const renderPreview = async () => {
    const result = await api('/api/markdown/render', {
      method:'POST',
      body: JSON.stringify({content: qs('#contentInput').value}),
    });
    const pane = qs('#previewPane');
    pane.innerHTML = result.html;
    pane.querySelectorAll('pre > code.language-mermaid').forEach(code => {
      const wrapper = document.createElement('div');
      wrapper.className = 'mermaid';
      wrapper.textContent = code.textContent;
      code.parentElement.replaceWith(wrapper);
    });
    if (window.mermaid) {
      try {
        await window.mermaid.run({nodes: pane.querySelectorAll('.mermaid')});
      } catch (_) {}
    }
  };

  const togglePreview = async () => {
    state.preview = !state.preview;
    qs('#contentInput').hidden = state.preview;
    qs('#previewPane').hidden = !state.preview;
    qs('#previewButton').textContent = state.preview ? 'Edit' : 'Preview';
    if (state.preview) await renderPreview();
  };

  const addChat = (role, text) => {
    const item = document.createElement('div');
    item.className = `chat-message ${role}`;
    item.textContent = text;
    qs('#chatLog').appendChild(item);
    qs('#chatLog').scrollTop = qs('#chatLog').scrollHeight;
  };

  const runSkill = async (skill) => {
    if (!state.noteId) return;
    addChat('user', `Skill: ${skill}`);
    addChat('assistant', 'Working…');
    const pending = qs('#chatLog').lastElementChild;
    try {
      const result = await api('/api/ai/skill', {
        method:'POST',
        body: JSON.stringify({note_id: state.noteId, skill}),
      });
      pending.remove();
      if (result.kind === 'answer') {
        addChat('assistant', result.value);
      } else {
        state.proposal = result;
        qs('#proposalText').textContent = Array.isArray(result.value) ? result.value.join(', ') : result.value;
        qs('#proposalCard').hidden = false;
        addChat('assistant', `I prepared a ${result.kind} proposal. Review it before applying.`);
      }
    } catch (err) {
      pending.textContent = err.message;
    }
  };

  const applyProposal = () => {
    if (!state.proposal) return;
    const {kind, value} = state.proposal;
    if (kind === 'content') qs('#contentInput').value = value;
    if (kind === 'title') qs('#titleInput').value = value;
    if (kind === 'tags') qs('#tagsInput').value = value.join(', ');
    qs('#proposalCard').hidden = true;
    state.proposal = null;
    scheduleSave();
    addChat('assistant', 'Proposal applied to the note and queued for autosave.');
  };

  const serverLabel = (url='') => {
    const clean = url.replace(/\/$/, '');
    if (clean === 'http://192.168.1.249:11434') return 'Ubuntu server';
    if (clean === 'http://127.0.0.1:11434') return 'Notes host';
    try { return new URL(clean).host || clean; } catch (_) { return clean || 'Ollama'; }
  };

  const updateAiModelLabel = (settings) => {
    const model = settings.model || 'No model';
    qs('#aiModelLabel').textContent = `${model} · ${serverLabel(settings.ollama_url)}`;
    qs('#aiModelLabel').title = settings.ollama_url || '';
  };

  const syncServerPreset = (url='') => {
    const preset = qs('#ollamaServerPreset');
    const clean = url.trim().replace(/\/$/, '');
    const known = [...preset.options].find(opt => opt.value !== 'custom' && opt.value === clean);
    preset.value = known ? known.value : 'custom';
  };

  const loadModels = async (selected='', url=qs('#ollamaUrlInput').value.trim()) => {
    const select = qs('#ollamaModelSelect');
    select.disabled = true;
    select.innerHTML = selected ? `<option value="${escapeHtml(selected)}">${escapeHtml(selected)}</option>` : '';
    qs('#aiSettingsStatus').textContent = `Loading models from ${serverLabel(url)}…`;
    try {
      const data = await api(`/api/ai/models?url=${encodeURIComponent(url)}`);
      const models = data.models || [];
      select.innerHTML = '';
      for (const model of models) {
        const opt = document.createElement('option');
        opt.value = model;
        opt.textContent = model;
        select.appendChild(opt);
      }
      if (!models.length && selected) {
        const opt = document.createElement('option');
        opt.value = selected;
        opt.textContent = selected;
        select.appendChild(opt);
      }
      select.value = models.includes(selected) ? selected : (models[0] || selected || '');
      qs('#aiSettingsStatus').textContent = `${models.length} model(s) on ${serverLabel(url)}`;
    } catch (err) {
      select.innerHTML = selected ? `<option value="${escapeHtml(selected)}">${escapeHtml(selected)}</option>` : '';
      qs('#aiSettingsStatus').textContent = err.message;
    } finally {
      select.disabled = false;
    }
  };

  const openSettings = async () => {
    qs('#settingsModal').hidden = false;
    const settings = await api('/api/ai/settings');
    qs('#ollamaUrlInput').value = settings.ollama_url;
    syncServerPreset(settings.ollama_url);
    qs('#embeddingModelInput').value = settings.embedding_model;
    qs('#aiTimeoutInput').value = settings.timeout_seconds;
    await loadModels(settings.model, settings.ollama_url);
  };

  const openHistory = async () => {
    if (!state.noteId) return;
    qs('#historyModal').hidden = false;
    const rows = await api(`/api/notes/${state.noteId}/versions`);
    const host = qs('#historyList');
    host.innerHTML = rows.length ? '' : '<div class="empty-state">No revisions yet. Revisions are captured before meaningful edits.</div>';
    for (const row of rows) {
      const item = document.createElement('div');
      item.className = 'history-item';
      item.innerHTML = `<strong>${escapeHtml(row.title)}</strong> <span class="muted">${new Date(row.created_at).toLocaleString()}</span><pre>${escapeHtml((row.content || '').slice(0, 1200))}</pre><button data-restore-version="${row.id}">Restore this revision</button>`;
      host.appendChild(item);
    }
  };

  const setupResizer = (el, side) => {
    el.addEventListener('pointerdown', (event) => {
      el.classList.add('dragging');
      el.setPointerCapture(event.pointerId);
      const move = (e) => {
        if (side === 'left') {
          const width = Math.max(220, Math.min(520, e.clientX));
          document.documentElement.style.setProperty('--sidebar-width', `${width}px`);
          localStorage.setItem('notes.sidebarWidth', width);
        } else {
          const width = Math.max(280, Math.min(620, window.innerWidth - e.clientX));
          document.documentElement.style.setProperty('--assistant-width', `${width}px`);
          localStorage.setItem('notes.assistantWidth', width);
        }
      };
      const up = () => {
        el.classList.remove('dragging');
        document.removeEventListener('pointermove', move);
        document.removeEventListener('pointerup', up);
      };
      document.addEventListener('pointermove', move);
      document.addEventListener('pointerup', up);
    });
  };

  document.addEventListener('click', async (event) => {
    const noteButton = event.target.closest('[data-note-id]');
    if (noteButton) return selectNote(Number(noteButton.dataset.noteId));

    const notebookButton = event.target.closest('.notebook-button');
    if (notebookButton) {
      qsa('.notebook-button').forEach(x => x.classList.remove('active'));
      notebookButton.classList.add('active');
      state.notebook = notebookButton.dataset.notebook;
      return refreshList();
    }

    const deleteAttachment = event.target.closest('[data-delete-attachment]');
    if (deleteAttachment) {
      if (!confirm('Remove this attachment?')) return;
      await api(`/api/attachments/${deleteAttachment.dataset.deleteAttachment}`, {method:'DELETE'});
      return selectNote(state.noteId);
    }

    const restoreVersion = event.target.closest('[data-restore-version]');
    if (restoreVersion) {
      if (!confirm('Restore this revision? The current version will be saved first.')) return;
      const note = await api(
        `/api/notes/${state.noteId}/versions/${restoreVersion.dataset.restoreVersion}/restore`,
        {method:'POST'}
      );
      qs('#historyModal').hidden = true;
      populateNote(note);
      await refreshList();
      return;
    }

    const skill = event.target.closest('[data-skill]');
    if (skill) return runSkill(skill.dataset.skill);

    if (event.target.classList.contains('modal-close')) {
      event.target.closest('.modal-backdrop').hidden = true;
    } else if (event.target.classList.contains('modal-backdrop')) {
      event.target.hidden = true;
    }
  });

  qsa('#titleInput, #contentInput, #tagsInput, #sourceUrlInput').forEach(el => el.addEventListener('input', scheduleSave));
  qs('#notebookSelect').addEventListener('change', scheduleSave);
  qs('#previewButton').addEventListener('click', togglePreview);

  qs('#newNoteButton').addEventListener('click', async () => {
    const note = await api('/api/notes', {method:'POST', body:'{}'});
    await refreshList();
    populateNote(note);
    qs('#titleInput').focus();
    qs('#titleInput').select();
  });

  qs('#searchInput').addEventListener('input', () => {
    clearTimeout(state.searchTimer);
    state.searchTimer = setTimeout(refreshList, 220);
  });

  qsa('.view-button').forEach(btn => btn.addEventListener('click', async () => {
    qsa('.view-button').forEach(x => x.classList.remove('active'));
    btn.classList.add('active');
    state.view = btn.dataset.view;
    await refreshList();
  }));

  qs('#addNotebookButton').addEventListener('click', async () => {
    const name = prompt('Notebook name');
    if (!name) return;
    const notebook = await api('/api/notebooks', {
      method:'POST',
      body: JSON.stringify({name}),
    });
    const btn = document.createElement('button');
    btn.className = 'notebook-button';
    btn.dataset.notebook = notebook.id;
    btn.textContent = notebook.name;
    qs('#notebookList').appendChild(btn);

    const opt = document.createElement('option');
    opt.value = notebook.id;
    opt.textContent = notebook.name;
    qs('#notebookSelect').appendChild(opt);
  });

  qs('#pinButton').addEventListener('click', async () => {
    if (!state.noteId) return;
    const note = await api(`/api/notes/${state.noteId}`, {
      method:'PATCH',
      body: JSON.stringify({pinned: !state.note.pinned}),
    });
    populateNote(note);
    await refreshList();
  });

  qs('#favouriteButton').addEventListener('click', async () => {
    if (!state.noteId) return;
    const note = await api(`/api/notes/${state.noteId}`, {
      method:'PATCH',
      body: JSON.stringify({favourite: !state.note.favourite}),
    });
    populateNote(note);
    await refreshList();
  });

  qs('#archiveButton').addEventListener('click', async () => {
    if (!state.noteId) return;
    const note = await api(`/api/notes/${state.noteId}/archive`, {
      method:'POST',
      body: JSON.stringify({archived: !state.note.archived}),
    });
    populateNote(note);
    await refreshList();
  });

  qs('#trashButton').addEventListener('click', async () => {
    if (!state.noteId) return;
    if (state.note.deleted) {
      const note = await api(`/api/notes/${state.noteId}/restore`, {method:'POST'});
      populateNote(note);
    } else {
      if (!confirm('Move this note to Trash?')) return;
      await api(`/api/notes/${state.noteId}/trash`, {method:'POST'});
      state.note = null;
      state.noteId = null;
      qs('#editorContent').hidden = true;
      qs('#editorEmpty').hidden = false;
    }
    await refreshList();
  });

  qs('#attachButton').addEventListener('click', () => state.noteId && qs('#attachmentInput').click());

  qs('#attachmentInput').addEventListener('change', async () => {
    const file = qs('#attachmentInput').files[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    setSaveState('Uploading…');
    try {
      await api(`/api/notes/${state.noteId}/attachments`, {method:'POST', body:form});
      await selectNote(state.noteId);
      setSaveState('Attachment added');
    } catch (err) {
      setSaveState(err.message);
    }
    qs('#attachmentInput').value = '';
  });

  qs('#historyButton').addEventListener('click', openHistory);
  qs('#exportButton').addEventListener('click', () => state.noteId && (window.location.href=`/export/note/${state.noteId}.md`));
  qs('#settingsButton').addEventListener('click', openSettings);
  qs('#ollamaServerPreset').addEventListener('change', async () => {
    const preset = qs('#ollamaServerPreset').value;
    if (preset === 'custom') {
      qs('#ollamaUrlInput').focus();
      qs('#ollamaUrlInput').select();
      return;
    }
    qs('#ollamaUrlInput').value = preset;
    await loadModels('', preset);
  });
  qs('#ollamaUrlInput').addEventListener('change', async () => {
    const url = qs('#ollamaUrlInput').value.trim();
    syncServerPreset(url);
    await loadModels('', url);
  });
  qs('#refreshModelsButton').addEventListener('click', () =>
    loadModels(qs('#ollamaModelSelect').value, qs('#ollamaUrlInput').value.trim())
  );

  qs('#saveSettingsButton').addEventListener('click', async () => {
    try {
      const data = await api('/api/ai/settings', {
        method:'POST',
        body: JSON.stringify({
          ollama_url: qs('#ollamaUrlInput').value,
          model: qs('#ollamaModelSelect').value,
          embedding_model: qs('#embeddingModelInput').value,
          timeout_seconds: Number(qs('#aiTimeoutInput').value),
        }),
      });
      qs('#aiSettingsStatus').textContent = `Saved — ${data.model} on ${serverLabel(data.ollama_url)}`;
      updateAiModelLabel(data);
    } catch (err) {
      qs('#aiSettingsStatus').textContent = err.message;
    }
  });

  qs('#testAiButton').addEventListener('click', async () => {
    qs('#aiSettingsStatus').textContent = 'Testing…';
    try {
      const data = await api('/api/ai/test', {
        method:'POST',
        body: JSON.stringify({
          ollama_url: qs('#ollamaUrlInput').value.trim(),
          model: qs('#ollamaModelSelect').value,
          timeout_seconds: Number(qs('#aiTimeoutInput').value),
        }),
      });
      qs('#aiSettingsStatus').textContent =
        `${data.response || 'Ready'} — ${data.model} on ${serverLabel(data.ollama_url)}`;
    } catch (err) {
      qs('#aiSettingsStatus').textContent = err.message;
    }
  });

  qs('#applyProposalButton').addEventListener('click', applyProposal);
  qs('#rejectProposalButton').addEventListener('click', () => {
    state.proposal = null;
    qs('#proposalCard').hidden = true;
    addChat('assistant', 'Proposal rejected.');
  });

  qs('#chatForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = qs('#chatInput').value.trim();
    if (!message) return;
    qs('#chatInput').value = '';
    addChat('user', message);
    addChat('assistant', 'Thinking…');
    const pending = qs('#chatLog').lastElementChild;
    try {
      const data = await api('/api/ai/chat', {
        method:'POST',
        body: JSON.stringify({
          message,
          note_id: state.noteId,
          scope: qs('#aiScope').value,
        }),
      });
      pending.textContent = data.answer;
    } catch (err) {
      pending.textContent = err.message;
    }
  });

  const storedTheme = localStorage.getItem('notes.theme') || 'light';
  document.documentElement.dataset.theme = storedTheme;
  qs('#themeToggle').addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('notes.theme', next);
  });

  document.addEventListener('keydown', (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      qs('#searchInput').focus();
      qs('#searchInput').select();
    }
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 's') {
      event.preventDefault();
      clearTimeout(state.saveTimer);
      saveNote();
    }
  });

  const sw = localStorage.getItem('notes.sidebarWidth');
  if (sw) document.documentElement.style.setProperty('--sidebar-width', `${sw}px`);
  const aw = localStorage.getItem('notes.assistantWidth');
  if (aw) document.documentElement.style.setProperty('--assistant-width', `${aw}px`);
  setupResizer(qs('#leftResizer'), 'left');
  setupResizer(qs('#rightResizer'), 'right');

  if (state.noteId) selectNote(state.noteId);
  api('/api/ai/settings')
    .then(updateAiModelLabel)
    .catch(() => {});
})();
