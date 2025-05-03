let editingIndex = null; // null means adding, otherwise it's editing

document.addEventListener('DOMContentLoaded', function () {
    const addButton = document.getElementById('addButton');
    const addOptions = document.getElementById('addOptions');
    const formPopup = document.getElementById('formPopup');
    const formTitle = document.getElementById('formTitle');
    const eventForm = document.getElementById('eventForm');
    const eventList = document.getElementById('eventList');
    const cancelButton = document.querySelector('#formPopup button[type="button"]'); // Target the cancel button
    
    let events = []; // Store events temporarily

    // Load events from backend
    function loadEvents() {
        const headerText = document.querySelector('h2').textContent;
        const [monthName, year] = headerText.split(' ');
        const monthNames = ["January", "February", "March", "April", "May", "June", 
                          "July", "August", "September", "October", "November", "December"];
        const month = monthNames.indexOf(monthName) + 1;

        fetch(`/get_events?year=${year}&month=${month}`)
            .then(response => response.json())
            .then(data => {
                events = data;
                renderEvents();
            })
            .catch(error => console.error('Error loading events:', error));
    }

    // Save events to backend
    function saveEvent(eventData) {
        return fetch('/save_event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(eventData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            if (data.success) {
                loadEvents(); // Reload events after saving
                return data;
            }
        })
        .catch(error => {
            console.error('Error saving event:', error);
            alert('Error saving event: ' + error.message);
        });
    }

    // Delete event from backend
    function deleteEventFromBackend(eventId) {
        return fetch('/delete_event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ event_id: eventId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadEvents(); // Reload events after deleting
            }
            return data;
        });
    }

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
    function openForm(type, index = null) {
        addOptions.classList.remove('show');
        formTitle.innerText = index === null ? "Add " + type : "Edit " + type;
        formPopup.classList.remove('hidden');
    
        if (index !== null) {
            // Pre-fill form fields
            const event = events[index];
            document.getElementById('title').value = event.title;
            document.getElementById('description').value = event.description;
            document.getElementById('eventDate').value = event.date || "";
            document.getElementById('eventTime').value = event.time || "";
            document.getElementById('recurrence').value = event.recurrence || "";
        } else {
            eventForm.reset();
        }
    
        editingIndex = index; // Track whether we are editing
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

    // Event form submission
    eventForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const title = document.getElementById('title').value;
        const description = document.getElementById('description').value;
        const date = document.getElementById('eventDate').value;
        const time = document.getElementById('eventTime').value;
        const recurrence = document.getElementById('recurrence').value;
        const eventType = document.querySelector('.option.show')?.dataset.type || "Event";

        // Get current date and time
        const now = new Date();
        const selectedDate = new Date(date);
        
        // Set the time for both dates to compare properly
        const [hours, minutes] = time.split(':').map(Number);
        selectedDate.setHours(hours, minutes, 0, 0);
        now.setHours(now.getHours(), now.getMinutes(), 0, 0);
        
        // Validate date and time
        if (selectedDate < now) {
            alert("You cannot select a past date and time.");
            return;
        }

        if (title.trim() !== "") {
            const eventData = {
                title: title.trim(),
                description: description.trim(),
                date: date,
                time: time,
                recurrence: recurrence,
                type: eventType
            };

            try {
                if (editingIndex === null) {
                    // Add new event
                    await saveEvent(eventData);
                } else {
                    // Edit existing event
                    const eventId = events[editingIndex]._id;
                    await saveEvent({ ...eventData, _id: eventId });
                }

                closeForm();
                eventForm.reset();
                editingIndex = null;
                loadEvents(); // Reload events after saving
            } catch (error) {
                console.error('Error in form submission:', error);
                alert('Error saving event: ' + error.message);
            }
        }
    });

    // Function to handle recurring events
    function handleRecurringEvents(event) {
        const eventDate = new Date(event.date);
        const currentMonth = parseInt(document.querySelector('h2').textContent.split(' ')[1]);
        const currentYear = parseInt(document.querySelector('h2').textContent.split(' ')[0]);
        
        switch(event.recurrence) {
            case 'daily':
                // Show icon for every day
                for (let day = 1; day <= 31; day++) {
                    const dayElement = document.getElementById(`event-icons-${day}`);
                    if (dayElement) {
                        addEventIcon(dayElement, event.type);
                    }
                }
                break;
                
            case 'weekly':
                // Show icon for the same day of the week
                const dayOfWeek = eventDate.getDay();
                const days = document.querySelectorAll('.day:not(.empty)');
                days.forEach(day => {
                    if (parseInt(day.textContent) % 7 === dayOfWeek) {
                        const dayElement = document.getElementById(`event-icons-${day.textContent.trim()}`);
                        if (dayElement) {
                            addEventIcon(dayElement, event.type);
                        }
                    }
                });
                break;
                
            case 'monthly':
                // Show icon for the same day of the month
                const dayOfMonth = eventDate.getDate();
                const dayElement = document.getElementById(`event-icons-${dayOfMonth}`);
                if (dayElement) {
                    addEventIcon(dayElement, event.type);
                }
                break;
                
            case 'yearly':
                // Show icon if it's the same month and day
                if (eventDate.getMonth() + 1 === currentMonth) {
                    const dayElement = document.getElementById(`event-icons-${eventDate.getDate()}`);
                    if (dayElement) {
                        addEventIcon(dayElement, event.type);
                    }
                }
                break;
                
            default:
                // For non-recurring events, show icon only on the specific date
                if (eventDate.getMonth() + 1 === currentMonth && eventDate.getFullYear() === currentYear) {
                    const dayElement = document.getElementById(`event-icons-${eventDate.getDate()}`);
                    if (dayElement) {
                        addEventIcon(dayElement, event.type);
                    }
                }
        }
    }

    // Helper function to add event icon
    function addEventIcon(dayElement, eventType) {
        const icon = document.createElement('i');
        icon.classList.add('fas', 
            eventType === "Reminder" ? "fa-bell" :
            eventType === "Task" ? "fa-check-circle" :
            "fa-star"
        );
        dayElement.appendChild(icon);
    }

    // Render saved events to the page
    function renderEvents() {
        eventList.innerHTML = '';
    
        if (events.length > 0) {
            document.getElementById('yourEventsHeading').style.display = 'block';
        } else {
            document.getElementById('yourEventsHeading').style.display = 'none';
        }
    
        // Clear all existing icons first
        document.querySelectorAll('.event-icons').forEach(iconContainer => {
            iconContainer.innerHTML = '';
        });
    
        events.forEach((ev, index) => {
            const eventDiv = document.createElement('div');
            eventDiv.classList.add('event-item');
            
            // Format the recurrence text
            let recurrenceText = ev.recurrence === 'none' ? 'No Recurrence' : 
                                ev.recurrence.charAt(0).toUpperCase() + ev.recurrence.slice(1);
            
            eventDiv.innerHTML = `
                <h3>${ev.title}</h3>
                <p>${ev.description}</p>
                <p><strong>Date:</strong> ${ev.date}</p>
                <p><strong>Time:</strong> ${ev.time}</p>
                <p><strong>Recurrence:</strong> ${recurrenceText}</p>
                <p><strong>Type:</strong> ${ev.type}</p>
                <div class="event-actions">
                    <button onclick="editEvent(${index})">Edit</button>
                    <button onclick="deleteEvent(${index})">Delete</button>
                </div>
            `;
            
            eventList.appendChild(eventDiv);
            
            // Handle recurring events
            handleRecurringEvents(ev);
        });
    }    

    // Delete event
    window.deleteEvent = function(index) {
        if (confirm("Are you sure you want to delete this event?")) {
            const eventId = events[index]._id;
            deleteEventFromBackend(eventId);
        }
    }

    // Edit event
    window.editEvent = function(index) {
        openForm('Event', index);
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

    // Initial load of events
    loadEvents();
});


// Function to handle the jump to a specific month and year
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


function deleteEvent(eventId) {
    // Remove the event from the database or data store
    events = events.filter(event => event.id !== eventId);

    // Remove the corresponding star on the calendar
    const eventStar = document.getElementById(`star-${eventId}`);
    if (eventStar) {
        eventStar.remove();
    }

    // Optionally, you can refresh the calendar to show the changes
    updateCalendar();
}


document.addEventListener('DOMContentLoaded', function() {
    const chatbotButton = document.getElementById('chatbotButton');
    const chatbotDropdown = document.getElementById('chatbotDropdown');
    const closeChatbotButton = document.getElementById('closeChatbot');
    const userMessageInput = document.getElementById('userMessage');
    const sendMessageButton = document.getElementById('sendMessageButton');
    const chatArea = document.getElementById('chatArea');

    // Toggle the chatbot dropdown visibility
    chatbotButton.addEventListener('click', function() {
        chatbotDropdown.classList.toggle('hidden');
    });

    // Close the chatbot dropdown
    closeChatbotButton.addEventListener('click', function() {
        chatbotDropdown.classList.add('hidden');
    });

    // Handle sending a message
    sendMessageButton.addEventListener('click', function() {
        const userMessage = userMessageInput.value.trim();

        if (userMessage) {
            // Add the user's message to the chat area
            const userMessageDiv = document.createElement('div');
            userMessageDiv.classList.add('user-message');
            userMessageDiv.textContent = `You: ${userMessage}`;
            chatArea.appendChild(userMessageDiv);

            // Send message to backend and get AI response
            fetch('/chat_with_ai', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Display the AI's response
                    const aiResponseDiv = document.createElement('div');
                    aiResponseDiv.classList.add('ai-message');
                    
                    // Format the response based on whether it's an event creation or regular message
                    let responseText = data.output_llm;
                    if (data.event_data) {
                        const eventType = data.event_data.type;
                        responseText = `I've created your ${eventType.toLowerCase()}: "${data.event_data.title}" on ${data.event_data.date} at ${data.event_data.time}`;
                    }
                    
                    aiResponseDiv.textContent = `AI: ${responseText}`;
                    chatArea.appendChild(aiResponseDiv);

                    // If there's event data, reload the events to show the new one
                    if (data.event_data) {
                        loadEvents();
                    }
                } else {
                    const errorDiv = document.createElement('div');
                    errorDiv.classList.add('ai-message', 'error');
                    errorDiv.textContent = `AI: ${data.error || 'An error occurred'}`;
                    chatArea.appendChild(errorDiv);
                }
                chatArea.scrollTop = chatArea.scrollHeight; // Scroll to the latest message
            })
            .catch(error => {
                console.error('Error:', error);
                const errorDiv = document.createElement('div');
                errorDiv.classList.add('ai-message', 'error');
                errorDiv.textContent = 'AI: Sorry, I encountered an error. Please try again.';
                chatArea.appendChild(errorDiv);
                chatArea.scrollTop = chatArea.scrollHeight;
            });
        }

        // Clear the input field after sending
        userMessageInput.value = '';
    });

    // Helper functions to extract event details from messages
    function extractTitle(message) {
        // Simple extraction - can be enhanced with more sophisticated parsing
        const titleMatch = message.match(/title:?\s*([^,]+)/i);
        return titleMatch ? titleMatch[1].trim() : 'New Event';
    }

    function extractDescription(message) {
        const descMatch = message.match(/description:?\s*([^,]+)/i);
        return descMatch ? descMatch[1].trim() : '';
    }

    function extractDate(message) {
        const dateMatch = message.match(/(\d{4}-\d{2}-\d{2})/);
        return dateMatch ? dateMatch[1] : new Date().toISOString().split('T')[0];
    }

    function extractTime(message) {
        const timeMatch = message.match(/(\d{1,2}:\d{2})/);
        return timeMatch ? timeMatch[1] : '00:00';
    }

    function extractType(message) {
        if (message.toLowerCase().includes('reminder')) return 'Reminder';
        if (message.toLowerCase().includes('task')) return 'Task';
        return 'Event';
    }

    // Close the dropdown if clicked outside the chatbot
    document.addEventListener('click', function(e) {
        if (!chatbotButton.contains(e.target) && !chatbotDropdown.contains(e.target)) {
            chatbotDropdown.classList.add('hidden');
        }
    });
});


const chatbotButton = document.getElementById('chatbotButton');
const chatbotDropdown = document.getElementById('chatbotDropdown');
const closeButton = document.getElementById('closeChatbot');

// Toggle dropdown visibility when the chatbot button is clicked
chatbotButton.addEventListener('click', function() {
    if (chatbotDropdown.style.display === 'none' || chatbotDropdown.style.display === '') {
        chatbotDropdown.style.display = 'block';  // Show the dropdown
    } else {
        chatbotDropdown.style.display = 'none';  // Hide the dropdown
    }
});

// Close the dropdown when the close button is clicked
closeButton.addEventListener('click', function() {
    chatbotDropdown.style.display = 'none';  // Hide the dropdown
});



// Signup and login 

// Fade out flash messages after a set time
setTimeout(() => {
    const flashMessages = document.querySelectorAll('.flash-messages li');
    flashMessages.forEach(message => {
        message.style.opacity = 0;
        setTimeout(() => {
            message.remove();
        }, 500); // Remove message after the fade-out transition
    });
}, 5000); // Adjust time as needed
