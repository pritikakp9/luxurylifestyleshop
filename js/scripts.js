// JavaScript for contact form submission handler and other utilities

// Handle contact form submission
function handleContactFormSubmission(event) {
    event.preventDefault(); // Prevent default form submission
    const formData = new FormData(event.target);
    fetch('https://your-backend-api.com/contact', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => console.log('Success:', data))
    .catch((error) => console.error('Error:', error));
}

// Chatbot opener function
function openChatbot() {
    const chatbot = document.getElementById('chatbot');
    chatbot.style.display = 'block'; // Show the chatbot
}

// Smooth scrolling for navigation links
const scrollLinks = document.querySelectorAll('a.scroll-link');
scrollLinks.forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault(); // Prevent default anchor click behavior
        const targetId = this.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        targetElement.scrollIntoView({ behavior: 'smooth' });
    });
});

// WhatsApp number updater
function updateWhatsAppNumber(newNumber) {
    const whatsappLink = document.getElementById('whatsapp-link');
    whatsappLink.href = `https://wa.me/${newNumber}`;
}

// Analytics logging
function logAnalytics(event) {
    // Assuming we have a logging endpoint
    fetch('https://your-analytics-api.com/log', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({event: event}),
    });
}

// Event listeners
document.getElementById('contact-form').addEventListener('submit', handleContactFormSubmission);

// Replace this with actual number
updateWhatsAppNumber('1234567890');

// Example logging
logAnalytics('Page Loaded');
