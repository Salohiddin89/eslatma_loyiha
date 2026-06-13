// ===== KUN TARTIBI — Main JS =====

function getCookie(name) {
  const val = document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith(name + '='));
  return val ? decodeURIComponent(val.split('=')[1]) : null;
}

function showToast(msg, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

// Live clock
function updateClock() {
  const el = document.getElementById('live-clock');
  if (!el) return;
  const now = new Date();
  const h = String(now.getHours()).padStart(2, '0');
  const m = String(now.getMinutes()).padStart(2, '0');
  el.textContent = `${h}:${m}`;
}
setInterval(updateClock, 1000);
updateClock();

// ===== CUSTOM CONFIRM MODAL =====
let _confirmCallback = null;

function openConfirmModal(title, msg, callback) {
  _confirmCallback = callback;
  document.getElementById('confirm-modal-title').textContent = title;
  document.getElementById('confirm-modal-msg').textContent = msg;
  document.getElementById('confirm-modal').classList.add('active');
}

function closeConfirmModal() {
  document.getElementById('confirm-modal').classList.remove('active');
  _confirmCallback = null;
}

document.getElementById('confirm-modal-ok')?.addEventListener('click', () => {
  const cb = _confirmCallback;
  closeConfirmModal();
  if (cb) cb();
});
document.getElementById('confirm-modal-cancel')?.addEventListener('click', closeConfirmModal);
document.getElementById('confirm-modal')?.addEventListener('click', e => {
  if (e.target === document.getElementById('confirm-modal')) closeConfirmModal();
});

// ===== ADD DAY MODAL =====
const addDayModal = document.getElementById('add-day-modal');
let selectedDay = null;

function openAddDayModal() {
  selectedDay = null;
  document.querySelectorAll('.day-select-btn').forEach(b => b.classList.remove('selected'));
  document.getElementById('day-title-input').value = '';
  addDayModal.classList.add('active');
}

function closeAddDayModal() {
  addDayModal.classList.remove('active');
}

document.querySelectorAll('.day-select-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    if (btn.disabled) return;
    document.querySelectorAll('.day-select-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    selectedDay = btn.dataset.day;
  });
});

document.getElementById('confirm-add-day')?.addEventListener('click', async () => {
  const title = document.getElementById('day-title-input').value.trim();
  if (!selectedDay) { showToast('Kunni tanlang', 'error'); return; }
  if (!title) { showToast('Kun nomini kiriting', 'error'); return; }

  try {
    const res = await fetch('/home/add-day/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ day: selectedDay, title })
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.error || 'Xato yuz berdi', 'error'); return; }

    const strip = document.getElementById('days-strip');
    const addBtn = document.getElementById('add-day-open-btn');
    const chip = document.createElement('a');
    chip.href = `/home/day/${data.day}/`;
    chip.className = 'day-chip';
    chip.dataset.day = data.day;
    chip.innerHTML = `<span class="day-dot"></span>${data.display}`;
    strip.insertBefore(chip, addBtn);

    const dayBtn = document.querySelector(`.day-select-btn[data-day="${data.day}"]`);
    if (dayBtn) dayBtn.disabled = true;

    closeAddDayModal();
    showToast(`${data.display} qo'shildi! 🎉`);
  } catch {
    showToast('Tarmoq xatosi', 'error');
  }
});

// ===== ADD REMINDER MODAL =====
const reminderModal = document.getElementById('reminder-modal');

function openReminderModal() {
  document.getElementById('reminder-title-input').value = '';
  document.getElementById('reminder-dt-input').value = '';
  reminderModal.classList.add('active');
}

function closeReminderModal() {
  reminderModal.classList.remove('active');
}

document.getElementById('confirm-add-reminder')?.addEventListener('click', async () => {
  const title = document.getElementById('reminder-title-input').value.trim();
  const dt = document.getElementById('reminder-dt-input').value;
  if (!title) { showToast('Eslatma nomini kiriting', 'error'); return; }
  if (!dt) { showToast('Vaqtni tanlang', 'error'); return; }

  try {
    const res = await fetch('/home/reminder/add/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ title, remind_at: dt })
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.error || 'Xato', 'error'); return; }

    const list = document.getElementById('reminders-list');
    const empty = list.querySelector('.empty-state');
    if (empty) empty.remove();

    const card = document.createElement('div');
    card.className = 'reminder-card';
    card.dataset.id = data.id;
    card.innerHTML = `
      <div class="reminder-icon">🔔</div>
      <div class="reminder-info">
        <div class="reminder-title">${data.title}</div>
        <div class="reminder-time">${data.remind_at}</div>
      </div>
      <button class="btn-edit" onclick="openEditReminderModal(${data.id}, '${data.title.replace(/'/g,"\\'")}', '${data.remind_at_input}')">✏️</button>
      <button class="btn-delete" onclick="confirmDeleteReminder(${data.id}, this)">🗑️</button>
    `;
    list.appendChild(card);
    closeReminderModal();
    showToast('Eslatma qo\'shildi! 🔔');
  } catch {
    showToast('Tarmoq xatosi', 'error');
  }
});

// ===== EDIT REMINDER MODAL =====
const editReminderModal = document.getElementById('edit-reminder-modal');

function openEditReminderModal(id, title, dtValue) {
  document.getElementById('edit-reminder-id').value = id;
  document.getElementById('edit-reminder-title-input').value = title;
  document.getElementById('edit-reminder-dt-input').value = dtValue;
  editReminderModal.classList.add('active');
}

function closeEditReminderModal() {
  editReminderModal.classList.remove('active');
}

document.getElementById('confirm-edit-reminder')?.addEventListener('click', async () => {
  const id = document.getElementById('edit-reminder-id').value;
  const title = document.getElementById('edit-reminder-title-input').value.trim();
  const dt = document.getElementById('edit-reminder-dt-input').value;
  if (!title) { showToast('Eslatma nomini kiriting', 'error'); return; }
  if (!dt) { showToast('Vaqtni tanlang', 'error'); return; }

  try {
    const res = await fetch(`/home/reminder/${id}/update/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ title, remind_at: dt })
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.error || 'Xato', 'error'); return; }

    const card = document.querySelector(`.reminder-card[data-id="${id}"]`);
    if (card) {
      card.querySelector('.reminder-title').textContent = data.title;
      card.querySelector('.reminder-time').textContent = data.remind_at;
      // update onclick attrs
      card.querySelector('.btn-edit').setAttribute('onclick',
        `openEditReminderModal(${data.id}, '${data.title.replace(/'/g,"\\'")}', '${data.remind_at_input}')`);
    }
    closeEditReminderModal();
    showToast('Eslatma yangilandi! ✅');
  } catch {
    showToast('Tarmoq xatosi', 'error');
  }
});

editReminderModal?.addEventListener('click', e => {
  if (e.target === editReminderModal) closeEditReminderModal();
});

// ===== DELETE REMINDER (with confirm) =====
function confirmDeleteReminder(id, btn) {
  openConfirmModal(
    'Eslatmani o\'chirish',
    'Haqiqatan ham bu eslatmani o\'chirmoqchimisiz?',
    async () => {
      try {
        const res = await fetch(`/home/reminder/${id}/delete/`, {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        if (res.ok) {
          btn.closest('.reminder-card').remove();
          showToast('Eslatma o\'chirildi');
        }
      } catch {
        showToast('Xato', 'error');
      }
    }
  );
}

// Keep old deleteReminder for any inline calls (used in dynamically added cards above)
async function deleteReminder(id, btn) {
  confirmDeleteReminder(id, btn);
}

// Close modals on overlay click
[addDayModal, reminderModal].forEach(m => {
  m?.addEventListener('click', e => {
    if (e.target === m) m.classList.remove('active');
  });
});

// ===== DAY DETAIL: ADD TASK =====
const taskModal = document.getElementById('task-modal');

function openTaskModal() {
  document.getElementById('task-title-input').value = '';
  document.getElementById('task-time-input').value = '';
  taskModal.classList.add('active');
}

function closeTaskModal() {
  taskModal.classList.remove('active');
}

document.getElementById('confirm-add-task')?.addEventListener('click', async () => {
  const title = document.getElementById('task-title-input').value.trim();
  const time = document.getElementById('task-time-input').value;
  if (!title) { showToast('Vazifa nomini kiriting', 'error'); return; }
  if (!time) { showToast('Vaqtni kiriting', 'error'); return; }

  const daySlug = document.getElementById('task-modal').dataset.day;

  try {
    const res = await fetch(`/home/day/${daySlug}/add-task/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ title, time })
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.error || 'Xato', 'error'); return; }

    const list = document.getElementById('tasks-list');
    const empty = list.querySelector('.empty-state');
    if (empty) empty.remove();

    const item = document.createElement('div');
    item.className = 'task-item';
    item.dataset.id = data.id;
    item.innerHTML = `
      <div class="task-time-badge">${data.time}</div>
      <div class="task-title">${data.title}</div>
      <button class="btn-edit" onclick="openEditTaskModal(${data.id}, '${data.title.replace(/'/g,"\\'")}', '${data.time}')">✏️</button>
      <button class="btn-delete" onclick="confirmDeleteTask(${data.id}, this)">🗑️</button>
    `;

    // Insert sorted by time
    const items = Array.from(list.querySelectorAll('.task-item'));
    const insertBefore = items.find(i => {
      const t = i.querySelector('.task-time-badge').textContent;
      return t > data.time;
    });
    if (insertBefore) list.insertBefore(item, insertBefore);
    else list.appendChild(item);

    closeTaskModal();
    showToast('Vazifa qo\'shildi! ✅');
  } catch {
    showToast('Tarmoq xatosi', 'error');
  }
});

// ===== EDIT TASK MODAL =====
const editTaskModal = document.getElementById('edit-task-modal');

function openEditTaskModal(id, title, time) {
  document.getElementById('edit-task-id').value = id;
  document.getElementById('edit-task-title-input').value = title;
  document.getElementById('edit-task-time-input').value = time;
  editTaskModal.classList.add('active');
}

function closeEditTaskModal() {
  editTaskModal.classList.remove('active');
}

document.getElementById('confirm-edit-task')?.addEventListener('click', async () => {
  const id = document.getElementById('edit-task-id').value;
  const title = document.getElementById('edit-task-title-input').value.trim();
  const time = document.getElementById('edit-task-time-input').value;
  if (!title) { showToast('Vazifa nomini kiriting', 'error'); return; }
  if (!time) { showToast('Vaqtni kiriting', 'error'); return; }

  try {
    const res = await fetch(`/home/task/${id}/update/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ title, time })
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.error || 'Xato', 'error'); return; }

    const item = document.querySelector(`.task-item[data-id="${id}"]`);
    if (item) {
      item.querySelector('.task-time-badge').textContent = data.time;
      item.querySelector('.task-title').textContent = data.title;
      item.querySelector('.btn-edit').setAttribute('onclick',
        `openEditTaskModal(${data.id}, '${data.title.replace(/'/g,"\\'")}', '${data.time}')`);
    }
    closeEditTaskModal();
    showToast('Vazifa yangilandi! ✅');
  } catch {
    showToast('Tarmoq xatosi', 'error');
  }
});

editTaskModal?.addEventListener('click', e => {
  if (e.target === editTaskModal) closeEditTaskModal();
});

// ===== DELETE TASK (with confirm) =====
function confirmDeleteTask(id, btn) {
  openConfirmModal(
    'Vazifani o\'chirish',
    'Haqiqatan ham bu vazifani o\'chirmoqchimisiz?',
    async () => {
      try {
        const res = await fetch(`/home/task/${id}/delete/`, {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        if (res.ok) {
          btn.closest('.task-item').remove();
          showToast('Vazifa o\'chirildi');
        }
      } catch {
        showToast('Xato', 'error');
      }
    }
  );
}

// ===== EDIT DAY MODAL =====
const editDayModal = document.getElementById('edit-day-modal');

function openEditDayModal(slug, title) {
  document.getElementById('edit-day-slug').value = slug;
  document.getElementById('edit-day-title-input').value = title;
  editDayModal.classList.add('active');
}

function closeEditDayModal() {
  editDayModal.classList.remove('active');
}

document.getElementById('confirm-edit-day')?.addEventListener('click', async () => {
  const slug = document.getElementById('edit-day-slug').value;
  const title = document.getElementById('edit-day-title-input').value.trim();
  if (!title) { showToast('Kun nomini kiriting', 'error'); return; }

  try {
    const res = await fetch(`/home/day/${slug}/update/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ title })
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.error || 'Xato', 'error'); return; }

    const subEl = document.getElementById('day-sub-title');
    if (subEl) subEl.textContent = data.title;

    // Update edit button onclick with new title
    const editBtn = document.querySelector('.edit-day-hero-btn');
    if (editBtn) editBtn.setAttribute('onclick', `openEditDayModal('${data.day}', '${data.title.replace(/'/g,"\\'")}')`);

    closeEditDayModal();
    showToast('Kun nomi yangilandi! ✅');
  } catch {
    showToast('Tarmoq xatosi', 'error');
  }
});

editDayModal?.addEventListener('click', e => {
  if (e.target === editDayModal) closeEditDayModal();
});

// ===== DELETE DAY (with confirm) =====
function confirmDeleteDay(slug) {
  openConfirmModal(
    'Kunni o\'chirish',
    'Haqiqatan ham bu kunni barcha vazifalari bilan o\'chirmoqchimisiz?',
    async () => {
      try {
        const res = await fetch(`/home/day/${slug}/delete/`, {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        if (res.ok) window.location.href = '/home/';
      } catch {
        showToast('Xato', 'error');
      }
    }
  );
}

taskModal?.addEventListener('click', e => {
  if (e.target === taskModal) closeTaskModal();
});

// Set min datetime for reminder input
const dtInput = document.getElementById('reminder-dt-input');
if (dtInput) {
  const now = new Date();
  now.setMinutes(now.getMinutes() + 5);
  dtInput.min = now.toISOString().slice(0, 16);
}

const editDtInput = document.getElementById('edit-reminder-dt-input');
if (editDtInput) {
  const now = new Date();
  now.setMinutes(now.getMinutes() + 1);
  editDtInput.min = now.toISOString().slice(0, 16);
}
