// Event type constants
const EVENT_TYPES = {
    EVENT: 'event',
    REMINDER: 'reminder',
    TASK: 'task'
};

let editingIndex = null; // null means adding, otherwise it's editing

document.addEventListener('DOMContentLoaded', function () {
    const addButton = document.getElementById('addButton');
    const addOptions = document.getElementById('addOptions');
    const formPopup = document.getElementById('formPopup');
    const formTitle = document.getElementById('formTitle');
    const eventForm = document.getElementById('eventForm');
    const eventList = document.getElementById('eventList');
    const cancelButton = document.querySelector('#formPopup button[type="button"]'); // Target the cancel button
    const chatbotButton = document.getElementById('chatbotButton');
    const chatbotDropdown = document.getElementById('chatbotDropdown');
    const closeChatbotButton = document.getElementById('closeChatbot');
    const userMessageInput = document.getElementById('userMessage');
    const sendMessageButton = document.getElementById('sendMessageButton');
    const chatArea = document.getElementById('chatArea');
    const jumpButton = document.getElementById('jumpButton');
    
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
                
                // Clear all existing icons first
                document.querySelectorAll('.event-icons').forEach(iconContainer => {
                    iconContainer.innerHTML = '';
                });
                
                // Add icons for all events
                events.forEach(event => {
                    handleRecurringEvents(event);
                });
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
        .then(async response => {
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Network response was not ok');
            }
            return data;
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
            throw error; // Re-throw to be caught by the form submission handler
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
        // Capitalize first letter for display
        const displayType = type.charAt(0).toUpperCase() + type.slice(1);
        formTitle.innerText = index === null ? "Add " + displayType : "Edit " + displayType;
        formPopup.classList.remove('hidden');
    
        if (index !== null) {
            // Pre-fill form fields
            const event = events[index];
            document.getElementById('title').value = event.title || '';
            document.getElementById('description').value = event.description || '';
            document.getElementById('eventDate').value = event.date || '';
            document.getElementById('eventTime').value = event.time || '';
            document.getElementById('recurrence').value = event.recurrence || 'none';
            
            // Set the correct event type in the form
            document.querySelectorAll('.option').forEach(opt => {
                opt.classList.remove('show');
                if (opt.dataset.type.toLowerCase() === event.type.toLowerCase()) {
                    opt.classList.add('show');
                }
            });
        } else {
            eventForm.reset();
            // Set the selected type in the form
            const selectedOption = document.querySelector(`.option[data-type="${type.toLowerCase()}"]`);
            if (selectedOption) {
                document.querySelectorAll('.option').forEach(opt => opt.classList.remove('show'));
                selectedOption.classList.add('show');
            }
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
        const eventType = document.querySelector('.option.show')?.dataset.type?.toLowerCase() || EVENT_TYPES.EVENT;

        // Validate event type
        if (!Object.values(EVENT_TYPES).includes(eventType)) {
            alert("Invalid event type. Please select a valid type.");
            return;
        }

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
                // Don't show alert here as it's already shown in saveEvent
                // Just keep the form open so user can try again
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
        // Get the day number from the parent element's ID
        const dayNumber = parseInt(dayElement.id.split('-')[2]);
        // Get the day of the week (0 = Sunday, 1 = Monday, etc.)
        const dayOfWeek = (dayNumber - 1) % 7;
        
        // Skip adding icon if it's a Sunday (dayOfWeek === 0)
        if (dayOfWeek === 0) {
            return;
        }
        
        const icon = document.createElement('i');
        icon.classList.add('fas', 
         
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
    
        // Group events by date
        const eventsByDate = {};
        events.forEach(event => {
            if (!eventsByDate[event.date]) {
                eventsByDate[event.date] = [];
            }
            eventsByDate[event.date].push(event);
        });

        // Sort dates
        const sortedDates = Object.keys(eventsByDate).sort();

        // Render events by date
        sortedDates.forEach(date => {
            const dateEvents = eventsByDate[date];
            
            // Create date header
            const dateHeader = document.createElement('div');
            dateHeader.classList.add('date-header');
            const formattedDate = new Date(date).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            dateHeader.innerHTML = `<h3>${formattedDate}</h3>`;
            eventList.appendChild(dateHeader);

            // Sort events by time for this date
            dateEvents.sort((a, b) => a.time.localeCompare(b.time));

            // Create events for this date
            dateEvents.forEach((ev, index) => {
                const eventDiv = document.createElement('div');
                eventDiv.classList.add('event-item');
                
                // Format the recurrence text
                let recurrenceText = (!ev.recurrence || ev.recurrence === 'none') 
                    ? 'No Recurrence' 
                    : ev.recurrence.charAt(0).toUpperCase() + ev.recurrence.slice(1);

                // Format the time
                const time = ev.time ? new Date(`2000-01-01T${ev.time}`).toLocaleTimeString('en-US', {
                    hour: 'numeric',
                    minute: '2-digit',
                    hour12: true
                }) : 'No time set';
                
                eventDiv.innerHTML = `
                    <div class="event-content">
                        <h4>${ev.title}</h4>
                        <p class="event-description">${ev.description}</p>
                        <div class="event-details">
                            <p><i class="far fa-clock"></i> ${time}</p>
                            <p><i class="fas fa-sync"></i> ${recurrenceText}</p>
                            <p><i class="fas fa-tag"></i> ${ev.type}</p>
                        </div>
                    </div>
                    <div class="event-actions">
                        <button onclick="editEvent(${events.indexOf(ev)})" class="edit-btn">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button onclick="deleteEvent(${events.indexOf(ev)})" class="delete-btn">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                `;
                
                eventList.appendChild(eventDiv);
            });
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
        const event = events[index];
        openForm(event.type, index);
    }

    // Adding event listeners for options (Event, Reminder, Task)
    const eventOption = document.querySelector('.option[data-type="event"]');
    const reminderOption = document.querySelector('.option[data-type="reminder"]');
    const taskOption = document.querySelector('.option[data-type="task"]');

    if (eventOption) {
        eventOption.addEventListener('click', () => openForm('Event'));
    }
    if (reminderOption) {
        reminderOption.addEventListener('click', () => openForm('Reminder'));
    }
    if (taskOption) {
        taskOption.addEventListener('click', () => openForm('Task'));
    }

    // Function to send message
    function sendMessage() {
        const userMessage = userMessageInput.value.trim();

        if (userMessage) {
            // Add the user's message to the chat area
            const userMessageDiv = document.createElement('div');
            userMessageDiv.classList.add('user-message');
            userMessageDiv.textContent = `You: ${userMessage}`;
            chatArea.appendChild(userMessageDiv);

            // Clear the input field after sending
            userMessageInput.value = '';

            // Send message to backend and get AI response
            fetch('/chat_with_ai', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('AI Response:', data); // Debug log
                
                // Display the AI's response
                const aiResponseDiv = document.createElement('div');
                aiResponseDiv.classList.add('ai-message');
                
                if (data.error) {
                    aiResponseDiv.classList.add('error');
                    aiResponseDiv.textContent = `AI: ${data.error}`;
                    console.error('AI Error:', data.error);
                } else {
                    // Display the output_llm from the backend
                    aiResponseDiv.textContent = `AI: ${data.output_llm}`;
                    
                    // If there's event data, update the calendar without refreshing the page
                    if (data.event_data) {
                        try {
                            // Add the new event to the events array
                            const newEvent = {
                                ...data.event_data,
                                _id: data.event_id // Add the event ID from the response
                            };
                            events.push(newEvent);
                            
                            // Update the event list
                            renderEvents();
                            
                            // Clear all existing icons first
                            document.querySelectorAll('.event-icons').forEach(iconContainer => {
                                iconContainer.innerHTML = '';
                            });
                            
                            // Update the calendar icons for all events
                            events.forEach(event => {
                                handleRecurringEvents(event);
                            });
                            
                            // Update the daily fact if it's a new day
                            updateDailyFact();
                        } catch (error) {
                            console.error('Error updating UI:', error);
                            aiResponseDiv.textContent = `AI: ${data.output_llm} (Note: There was an error updating the display, but your event was created successfully. Please refresh the page to see it.)`;
                        }
                    }
                }
                
                chatArea.appendChild(aiResponseDiv);
                chatArea.scrollTop = chatArea.scrollHeight; // Scroll to the latest message
            })
            .catch(error => {
                console.error('Error:', error);
                const errorDiv = document.createElement('div');
                errorDiv.classList.add('ai-message', 'error');
                errorDiv.textContent = `AI: ${error.message || 'An error occurred while processing your request. Please try again.'}`;
                chatArea.appendChild(errorDiv);
                chatArea.scrollTop = chatArea.scrollHeight;
            });
        }
    }

    // Send message when clicking the send button
    sendMessageButton.addEventListener('click', sendMessage);

    // Send message when pressing Enter
    userMessageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Toggle the chatbot dropdown visibility with animation
    chatbotButton.addEventListener('click', function() {
        chatbotDropdown.classList.toggle('hidden');
        if (!chatbotDropdown.classList.contains('hidden')) {
            userMessageInput.focus();
        }
    });

    // Close the chatbot dropdown
    closeChatbotButton.addEventListener('click', function() {
        chatbotDropdown.classList.add('hidden');
    });

    // Close the dropdown if clicked outside the chatbot
    document.addEventListener('click', function(e) {
        if (!chatbotButton.contains(e.target) && 
            !chatbotDropdown.contains(e.target) && 
            !chatbotDropdown.classList.contains('hidden')) {
            chatbotDropdown.classList.add('hidden');
        }
    });

    // Add welcome message when opening the chat
    chatbotButton.addEventListener('click', function() {
        if (!chatbotDropdown.classList.contains('hidden') && chatArea.children.length === 0) {
            // Load chat history when opening the chat
            fetch('/get_chat_history')
                .then(response => response.json())
                .then(data => {
                    if (data.history && data.history.length > 0) {
                        // Display chat history
                        data.history.forEach(msg => {
                            const messageDiv = document.createElement('div');
                            messageDiv.classList.add(msg.role === 'user' ? 'user-message' : 'ai-message');
                            messageDiv.textContent = `${msg.role === 'user' ? 'You' : 'AI'}: ${msg.content}`;
                            chatArea.appendChild(messageDiv);
                        });
                    } else {
                        // Display welcome message if no history
                        const welcomeDiv = document.createElement('div');
                        welcomeDiv.classList.add('ai-message');
                        welcomeDiv.textContent = 'AI: Hello! I\'m your calendar assistant. How can I help you today?';
                        chatArea.appendChild(welcomeDiv);
                    }
                    chatArea.scrollTop = chatArea.scrollHeight;
                })
                .catch(error => {
                    console.error('Error loading chat history:', error);
                    // Display welcome message if there's an error
                    const welcomeDiv = document.createElement('div');
                    welcomeDiv.classList.add('ai-message');
                    welcomeDiv.textContent = 'AI: Hello! I\'m your calendar assistant. How can I help you today?';
                    chatArea.appendChild(welcomeDiv);
                });
        }
    });

    // Function to update daily fact
    function updateDailyFact() {
        return new Promise((resolve, reject) => {
            const factElement = document.querySelector('.daily-fact');
            if (factElement) {
                factElement.textContent = 'Loading...';
            }
            
            fetch('/get_daily_fact')
                .then(response => response.json())
                .then(data => {
                    if (data.fact) {
                        if (factElement) {
                            factElement.textContent = data.fact;
                        }
                    }
                    resolve();
                })
                .catch(error => {
                    console.error('Error updating daily fact:', error);
                    if (factElement) {
                        factElement.textContent = 'Unable to load daily fact';
                    }
                    resolve(); // Still resolve to allow navigation
                });
        });
    }

    // Add jump button event listener
    if (jumpButton) {
        jumpButton.addEventListener('click', () => {
            const month = document.getElementById('jumpMonth').value;
            const year = document.getElementById('jumpYear').value;

            if (year > 0) {
                // Update the daily fact before changing the page
                updateDailyFact().then(() => {
                    window.location.href = `/calendar/${year}/${month}`;
                });
            } else {
                alert("Please enter a valid year.");
            }
        });
    }

    // Initial load of events
    loadEvents();
});


// Add event listeners for month navigation
document.addEventListener('DOMContentLoaded', function() {
    const prevMonthButton = document.querySelector('.prev-month');
    const nextMonthButton = document.querySelector('.next-month');
    
    if (prevMonthButton) {
        prevMonthButton.addEventListener('click', (e) => {
            e.preventDefault();
            const currentUrl = window.location.pathname;
            const match = currentUrl.match(/\/calendar\/(\d+)\/(\d+)/);
            if (match) {
                let [_, year, month] = match;
                year = parseInt(year);
                month = parseInt(month);
                
                if (month === 1) {
                    year--;
                    month = 12;
                } else {
                    month--;
                }
                
                updateDailyFact().then(() => {
                    window.location.href = `/calendar/${year}/${month}`;
                });
            }
        });
    }
    
    if (nextMonthButton) {
        nextMonthButton.addEventListener('click', (e) => {
            e.preventDefault();
            const currentUrl = window.location.pathname;
            const match = currentUrl.match(/\/calendar\/(\d+)\/(\d+)/);
            if (match) {
                let [_, year, month] = match;
                year = parseInt(year);
                month = parseInt(month);
                
                if (month === 12) {
                    year++;
                    month = 1;
                } else {
                    month++;
                }
                
                updateDailyFact().then(() => {
                    window.location.href = `/calendar/${year}/${month}`;
                });
            }
        });
    }
    
    // Initial load of daily fact
    updateDailyFact();
});


function deleteEvent(eventId) {
    if (confirm("Are you sure you want to delete this event?")) {
        fetch('/delete_event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ event_id: eventId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the event from the events array
                events = events.filter(event => event._id !== eventId);
                
                // Update the UI
                renderEvents();
                
                // Clear and update calendar icons
                document.querySelectorAll('.event-icons').forEach(iconContainer => {
                    iconContainer.innerHTML = '';
                });
                events.forEach(event => {
                    handleRecurringEvents(event);
                });
            }
        })
        .catch(error => console.error('Error deleting event:', error));
    }
}



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


