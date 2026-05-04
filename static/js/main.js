// ========================================
// ShieldDFL - Interactive JavaScript
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize animations
    initAnimations();
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize smooth scrolling
    initSmoothScroll();
    
    // Initialize card animations
    initCardAnimations();
    
    // Initialize counter animations
    initCounterAnimations();
    
    // Initialize page transitions
    initPageTransitions();
    
    // Initialize table row animations
    initTableAnimations();
    
    // Auto-dismiss alerts
    autoDismissAlerts();
    
    // Initialize loading states
    initLoadingStates();
});

// ========================================
// ANIMATION INITIALIZATION
// ========================================
function initAnimations() {
    // Add fade-in animation to main content
    const container = document.querySelector('.container');
    if (container) {
        container.classList.add('page-transition');
    }
    
    // Stagger card animations
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
}

// ========================================
// TOOLTIPS
// ========================================
function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            animation: true,
            delay: { show: 500, hide: 100 }
        });
    });
}

// ========================================
// SMOOTH SCROLLING
// ========================================
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href !== '#navbarNav') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

// ========================================
// CARD ANIMATIONS
// ========================================
function initCardAnimations() {
    const cards = document.querySelectorAll('.card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateY(30px)';
                
                setTimeout(() => {
                    entry.target.style.transition = 'all 0.6s ease-out';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, 100);
                
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    cards.forEach(card => observer.observe(card));
}

// ========================================
// COUNTER ANIMATIONS
// ========================================
function initCounterAnimations() {
    const counters = document.querySelectorAll('.stat-number');
    
    const animateCounter = (counter) => {
        const target = parseInt(counter.textContent.replace(/,/g, ''));
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;
        
        const updateCounter = () => {
            current += increment;
            if (current < target) {
                counter.textContent = Math.floor(current).toLocaleString();
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target.toLocaleString();
            }
        };
        
        updateCounter();
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    counters.forEach(counter => observer.observe(counter));
}

// ========================================
// PAGE TRANSITIONS
// ========================================
function initPageTransitions() {
    // Add loading animation when clicking links
    document.querySelectorAll('a:not([href^="#"]):not([target="_blank"])').forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href && !href.startsWith('javascript:') && !this.hasAttribute('data-bs-toggle')) {
                e.preventDefault();
                
                // Fade out current page
                document.body.style.transition = 'opacity 0.3s ease-out';
                document.body.style.opacity = '0';
                
                // Navigate after animation
                setTimeout(() => {
                    window.location.href = href;
                }, 300);
            }
        });
    });
}

// ========================================
// TABLE ANIMATIONS
// ========================================
function initTableAnimations() {
    const rows = document.querySelectorAll('.table tbody tr');
    
    rows.forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateX(-20px)';
        
        setTimeout(() => {
            row.style.transition = 'all 0.4s ease-out';
            row.style.opacity = '1';
            row.style.transform = 'translateX(0)';
        }, index * 50);
    });
    
    // Add click effect
    rows.forEach(row => {
        row.addEventListener('click', function() {
            this.style.transition = 'all 0.2s ease';
            this.style.transform = 'scale(1.02)';
            
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 200);
        });
    });
}

// ========================================
// AUTO-DISMISS ALERTS
// ========================================
function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// ========================================
// LOADING STATES
// ========================================
function initLoadingStates() {
    // Show loading spinner on form submission
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Loading...
                `;
                
                // Reset after 10 seconds (fallback)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 10000);
            }
        });
    });
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

// Show notification
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success');
    }).catch(err => {
        showNotification('Failed to copy', 'danger');
    });
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ========================================
// REAL-TIME UPDATE ANIMATIONS
// ========================================

// Highlight updated rows
function highlightUpdatedRow(row) {
    row.style.transition = 'background-color 0.5s ease';
    row.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
    
    setTimeout(() => {
        row.style.backgroundColor = '';
    }, 2000);
}

// Pulse animation for new data
function pulseElement(element) {
    element.style.animation = 'pulse 0.5s ease';
    
    setTimeout(() => {
        element.style.animation = '';
    }, 500);
}

// Progressive loading for large tables
function progressiveTableLoad(tableBody, rows, batchSize = 10) {
    let index = 0;
    
    function loadBatch() {
        const batch = rows.slice(index, index + batchSize);
        batch.forEach((rowData, i) => {
            const row = document.createElement('tr');
            row.innerHTML = rowData;
            row.style.opacity = '0';
            row.style.transform = 'translateY(20px)';
            tableBody.appendChild(row);
            
            setTimeout(() => {
                row.style.transition = 'all 0.3s ease';
                row.style.opacity = '1';
                row.style.transform = 'translateY(0)';
            }, i * 50);
        });
        
        index += batchSize;
        
        if (index < rows.length) {
            setTimeout(loadBatch, 100);
        }
    }
    
    loadBatch();
}

// ========================================
// CHART ANIMATIONS (if using charts)
// ========================================
function animateChart(chart) {
    chart.style.opacity = '0';
    chart.style.transform = 'scale(0.8)';
    
    setTimeout(() => {
        chart.style.transition = 'all 0.6s ease-out';
        chart.style.opacity = '1';
        chart.style.transform = 'scale(1)';
    }, 100);
}

// ========================================
// EXPORT FUNCTIONS FOR GLOBAL USE
// ========================================
window.ShieldDFL = {
    showNotification,
    copyToClipboard,
    formatNumber,
    highlightUpdatedRow,
    pulseElement,
    progressiveTableLoad,
    animateChart,
    debounce
};

// ========================================
// LOADING SCREEN
// ========================================
window.addEventListener('load', function() {
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease-in';
        document.body.style.opacity = '1';
    }, 100);
});

// ========================================
// PERFORMANCE MONITORING
// ========================================
if (window.performance && window.performance.timing) {
    window.addEventListener('load', function() {
        const loadTime = window.performance.timing.domContentLoadedEventEnd - window.performance.timing.navigationStart;
        console.log(`Page loaded in ${loadTime}ms`);
        
        if (loadTime > 3000) {
            console.warn('Page load time is slow. Consider optimization.');
        }
    });
}
