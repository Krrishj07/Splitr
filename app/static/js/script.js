// Simple JavaScript for beginners

// Wait for the page to load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded!');
    
    // Add a simple animation to buttons
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 100);
        });
    });
    
    // Simple form validation
    const contactForm = document.querySelector('form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const message = document.getElementById('message').value;
            
            if (name.length < 2) {
                alert('Please enter a valid name (at least 2 characters)');
                e.preventDefault();
                return;
            }
            
            if (!email.includes('@')) {
                alert('Please enter a valid email address');
                e.preventDefault();
                return;
            }
            
            if (message.length < 10) {
                alert('Please enter a message (at least 10 characters)');
                e.preventDefault();
                return;
            }
            
            // If everything is valid, show a loading message
            const submitButton = this.querySelector('button');
            submitButton.textContent = 'Sending...';
        });
    }
    
    // Add hover effect to navigation links
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#555';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'transparent';
        });
    });
});

// Simple function to show an alert
function showAlert(message) {
    alert(message);
}