document.addEventListener('DOMContentLoaded', function () {
    const addButton = document.getElementById('addButton');
    const addOptions = document.getElementById('addOptions');
    const formPopup = document.getElementById('formPopup');
    const formTitle = document.getElementById('formTitle');
    const eventForm = document.getElementById('eventForm');
    const eventList = document.getElementById('eventList');
    const cancelButton = document.querySelector('#formPopup button[type="button"]'); // Target the cancel button

    let events = []; // Store events temporarily

    // Toggle dropdown for event, reminder, task
    addButton.addEventListener('click', (e) => {
        e.stopPropagation();  // Prevent event propagation to document listener
        addOptions.classList.toggle('show');  // Toggle the dropdown
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!addButton.contains(e.target) && !addOptions.contains(e.target)) {
            addOptions.classList.remove('show');  // Close the dropdown if clicked outside
        }
    });

    // Open the form for event, reminder, or task
    function openForm(type) {
        addOptions.classList.remove('show');  // Close the dropdown when a selection is made
        formTitle.innerText = "Add " + type;  // Update form title based on selection
        formPopup.classList.remove('hidden');  // Show the form popup
    }

    // Close the form when the cancel button is clicked
    function closeForm() {
        formPopup.classList.add('hidden');  // Hide the form popup
    }

    // Cancel button event listener
    if (cancelButton) {
        cancelButton.addEventListener('click', () => {
            closeForm();  // Call closeForm() when cancel is clicked
            eventForm.reset();  // Reset the form fields
        });
    }

    // Save event when submitting the form
    eventForm.addEventListener('submit', function(e) {
        e.preventDefault();  // Prevent default form submission
        const title = document.getElementById('title').value;
        const description = document.getElementById('description').value;

        // Only save the event if the title is not empty
        if (title.trim() !== "") {
            events.push({ title, description });
            renderEvents();  // Render the events list
            closeForm();  // Close the form
            eventForm.reset();  // Reset the form fields
        }
    });

    // Render saved events to the page
    function renderEvents() {
        eventList.innerHTML = '';  // Clear existing events
        events.forEach((ev) => {
            const eventDiv = document.createElement('div');
            eventDiv.classList.add('event-item');
            eventDiv.innerHTML = `<h3>${ev.title}</h3><p>${ev.description}</p>`;
            eventList.appendChild(eventDiv);  // Append event to the list
        });
    }

    // Adding event listeners for options (Event, Reminder, Task)
    const eventOption = document.querySelector('.option[data-type="Event"]');
    const reminderOption = document.querySelector('.option[data-type="Reminder"]');
    const taskOption = document.querySelector('.option[data-type="Task"]');

    if (eventOption) {
        eventOption.addEventListener('click', () => openForm('Event'));
    }
    if (reminderOption) {
        reminderOption.addEventListener('click', () => openForm('Reminder'));
    }
    if (taskOption) {
        taskOption.addEventListener('click', () => openForm('Task'));
    }
});


// Jump to a specific month and year
const jumpButton = document.getElementById('jumpButton');

jumpButton.addEventListener('click', () => {
    const month = document.getElementById('jumpMonth').value;
    const year = document.getElementById('jumpYear').value;

    if (year > 0) {
        window.location.href = `/calendar/${year}/${month}`;
    } else {
        alert("Please enter a valid year.");
    }
});
