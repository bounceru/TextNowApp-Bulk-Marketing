/**
 * Campaign Scheduler JavaScript for TextNow Max
 * 
 * This file handles the interactive elements of the campaign schedule page.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize interactive elements
    initCampaignScheduler();
});

/**
 * Initialize all campaign scheduler functionality
 */
function initCampaignScheduler() {
    // Set up distribution pattern change handlers
    setupDistributionPatternHandlers();
    
    // Set up date input defaults
    setupDateDefaults();
    
    // Hook up schedule creation form
    setupScheduleForm();
    
    // Hook up action buttons (pause, clone, etc.)
    setupActionButtons();
}

/**
 * Set up distribution pattern change handlers
 */
function setupDistributionPatternHandlers() {
    const patternSelect = document.getElementById('distribution-pattern');
    if (!patternSelect) return;
    
    patternSelect.addEventListener('change', function() {
        updateDistributionPreview();
    });
    
    // Set up time input change handlers
    const startTimeInput = document.getElementById('start-time');
    const endTimeInput = document.getElementById('end-time');
    const messagesInput = document.getElementById('total-messages');
    
    if (startTimeInput && endTimeInput && messagesInput) {
        startTimeInput.addEventListener('change', updateDistributionPreview);
        endTimeInput.addEventListener('change', updateDistributionPreview);
        messagesInput.addEventListener('input', updateDistributionPreview);
    }
    
    // Initial update
    updateDistributionPreview();
}

/**
 * Set up date input defaults
 */
function setupDateDefaults() {
    const startDateInput = document.getElementById('start-date');
    if (startDateInput) {
        // Set default to today if not already set
        if (!startDateInput.value) {
            const today = new Date();
            startDateInput.value = today.toISOString().split('T')[0];
        }
    }
}

/**
 * Set up schedule creation form
 */
function setupScheduleForm() {
    const scheduleForm = document.getElementById('schedule-form');
    if (!scheduleForm) return;
    
    scheduleForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(scheduleForm);
        const jsonData = {};
        
        for (const [key, value] of formData.entries()) {
            jsonData[key] = value;
        }
        
        // Add any complex options
        const advancedOptions = {
            accountHealth: document.getElementById('account_health')?.checked || false,
            dynamicAdjust: document.getElementById('dynamic_adjust')?.checked || false,
            rateLimiting: document.getElementById('rate_limiting')?.checked || false,
            errorCorrection: document.getElementById('error_correction')?.checked || false
        };
        
        jsonData.advancedOptions = JSON.stringify(advancedOptions);
        
        // Submit to backend
        fetch('/api/schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Schedule created successfully!');
                window.location.reload();
            } else {
                alert('Error creating schedule: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error creating schedule. Please try again.');
        });
    });
}

/**
 * Set up action buttons for existing schedules
 */
function setupActionButtons() {
    // Pause/Resume buttons
    document.querySelectorAll('.pause-schedule-btn').forEach(button => {
        button.addEventListener('click', function() {
            const scheduleId = this.dataset.scheduleId;
            const action = this.dataset.action; // 'pause' or 'resume'
            
            fetch(`/api/schedule/${scheduleId}/${action}`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert(`Error ${action}ing schedule: ${data.error}`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert(`Error ${action}ing schedule. Please try again.`);
            });
        });
    });
    
    // Clone buttons
    document.querySelectorAll('.clone-schedule-btn').forEach(button => {
        button.addEventListener('click', function() {
            const scheduleId = this.dataset.scheduleId;
            const scheduleName = this.dataset.scheduleName;
            
            const newName = prompt('Enter name for the cloned schedule:', `${scheduleName} (Copy)`);
            if (!newName) return;
            
            fetch(`/api/schedule/${scheduleId}/clone`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: newName })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert(`Error cloning schedule: ${data.error}`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error cloning schedule. Please try again.');
            });
        });
    });
    
    // Delete buttons
    document.querySelectorAll('.delete-schedule-btn').forEach(button => {
        button.addEventListener('click', function() {
            const scheduleId = this.dataset.scheduleId;
            const scheduleName = this.dataset.scheduleName;
            
            if (confirm(`Are you sure you want to delete the schedule "${scheduleName}"?`)) {
                fetch(`/api/schedule/${scheduleId}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        alert(`Error deleting schedule: ${data.error}`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error deleting schedule. Please try again.');
                });
            }
        });
    });
}

/**
 * Update the distribution preview based on current form values
 */
function updateDistributionPreview() {
    const pattern = document.getElementById('distribution-pattern')?.value || 'bell';
    const startTime = document.getElementById('start-time')?.value || '08:00';
    const endTime = document.getElementById('end-time')?.value || '20:00';
    const totalMessages = parseInt(document.getElementById('total-messages')?.value || '100000');
    
    // Convert time strings to hours
    const startHour = parseInt(startTime.split(':')[0]);
    const endHour = parseInt(endTime.split(':')[0]);
    
    const previewContainer = document.getElementById('distribution-preview');
    if (!previewContainer) return;
    
    // Fetch preview data from backend
    fetch('/api/schedule/preview-distribution', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            pattern,
            startHour,
            endHour,
            totalMessages
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.visualization) return;
        
        // Update visualization
        updateDistributionVisualization(data.visualization, data.stats);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

/**
 * Update the distribution visualization based on data
 */
function updateDistributionVisualization(visualization, stats) {
    const previewContainer = document.getElementById('distribution-preview');
    if (!previewContainer) return;
    
    // Create bars
    let barsHtml = '';
    
    visualization.forEach(item => {
        const heightPercentage = (item.count / stats.peak_count) * 100;
        
        barsHtml += `
            <div class="distribution-bar" style="height: ${heightPercentage}%;" title="${item.count} messages at ${item.display_hour}">
                <div class="bar-label">${item.display_hour}</div>
            </div>
        `;
    });
    
    // Create stats
    const statsHtml = `
        <div class="distribution-stats">
            <div>Peak: ${stats.peak_count} messages at ${formatHour(stats.peak_hour)}</div>
            <div>Average: ${stats.avg_per_hour} messages per hour</div>
        </div>
    `;
    
    previewContainer.innerHTML = `
        <div class="distribution-graph">
            ${barsHtml}
        </div>
        ${statsHtml}
    `;
}

/**
 * Format hour for display
 */
function formatHour(hour) {
    if (hour === 0) return "12am";
    if (hour < 12) return `${hour}am`;
    if (hour === 12) return "12pm";
    return `${hour-12}pm`;
}