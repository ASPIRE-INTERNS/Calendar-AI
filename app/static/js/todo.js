document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("todo-container");
  const addListBtn = document.getElementById("add-list-btn");

  function fetchLists() {
    fetch('/api/todo-lists')
      .then(res => res.json())
      .then(renderTodoLists);
  }

  function renderTodoLists(lists) {
    container.innerHTML = '';
    lists.forEach(list => {
      const div = document.createElement('div');
      div.classList.add('todo-list-card');
      div.innerHTML = `
        <div class="todo-list-header">
          <input value="${list.name}" data-id="${list._id}" class="todo-list-title list-name" />
          <div class="todo-list-actions">
            <button class="delete-btn delete-list" data-id="${list._id}">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
        <ul class="todo-items">
          ${list.items.map((item, i) => `
            <li class="todo-item${item.completed ? ' completed' : ''}">
              <input type="checkbox" ${item.completed ? 'checked' : ''} data-id="${list._id}" data-index="${i}" class="todo-checkbox tick-item"/>
              <span class="todo-text">${item.text}</span>
              <div class="todo-item-actions">
                <button data-id="${list._id}" data-index="${i}" class="delete-btn delete-item">
                    <i class="fas fa-trash"></i>
                </button>
              </div>
            </li>`).join('')}
        </ul>
        <input placeholder="New item..." class="new-item-input" data-id="${list._id}" />
      `;
      container.appendChild(div);
    });
  }

  // Add new list
  addListBtn.addEventListener("click", () => {
    const name = prompt("Enter name for the new list:");
    if (!name) return;
    fetch('/api/todo-list', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    }).then(fetchLists);
  });

  // Delegate events
  container.addEventListener('change', e => {
    if (e.target.classList.contains('tick-item')) {
      fetch(`/api/todo-list/${e.target.dataset.id}/item/${e.target.dataset.index}`, {
        method: 'PUT'
      }).then(fetchLists);
    }
  });

  container.addEventListener('click', async e => {
    // Always get the button, even if an icon inside is clicked
    const deleteItemBtn = e.target.closest('.delete-item');
    const deleteListBtn = e.target.closest('.delete-list');

    if (deleteItemBtn) {
      await fetch(`/api/todo-list/${deleteItemBtn.dataset.id}/item/${deleteItemBtn.dataset.index}`, {
        method: 'DELETE'
      });
      fetchLists();
    }

    if (deleteListBtn) {
      if (confirm("Are you sure you want to delete this entire list?")) {
        await fetch(`/api/todo-list/${deleteListBtn.dataset.id}`, {
          method: 'DELETE'
        });
        fetchLists();
      }
    }
  });

  container.addEventListener('keypress', e => {
    if (e.target.classList.contains('new-item-input') && e.key === 'Enter') {
      const text = e.target.value.trim();
      const id = e.target.dataset.id;
      if (text) {
        fetch(`/api/todo-list/${id}/item`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        }).then(fetchLists);
        e.target.value = '';
      }
    }
  });

  container.addEventListener('blur', e => {
    if (e.target.classList.contains('list-name')) {
      const id = e.target.dataset.id;
      const newName = e.target.value;
      fetch(`/api/todo-list/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName })
      });
    }
  }, true);

  // Only call fetchLists once on load
  fetchLists(); // initial render

  if (window.fetchLists) {
    fetchLists(); // This will refresh the to-do list container
  }
});
