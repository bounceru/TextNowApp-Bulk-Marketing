// TextNow Max Creator - Real API Integration

// Override the demo API calls with real functionality
window.realAPI = {
    createAccounts: function(count, areaCodes) {
        return fetch('/api/real/create_accounts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ count, area_codes: areaCodes })
        }).then(response => response.json());
    },
    
    getAccounts: function(status, limit, offset) {
        let url = '/api/real/accounts';
        let params = new URLSearchParams();
        
        if (status) params.append('status', status);
        if (limit) params.append('limit', limit);
        if (offset) params.append('offset', offset);
        
        if (params.toString()) url += '?' + params.toString();
        
        return fetch(url).then(response => response.json());
    },
    
    getAccount: function(accountId) {
        return fetch(`/api/real/accounts/${accountId}`).then(response => response.json());
    },
    
    sendMessage: function(accountId, recipient, message) {
        return fetch('/api/real/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account_id: accountId, recipient, message })
        }).then(response => response.json());
    },
    
    rotateIP: function() {
        return fetch('/api/real/rotate_ip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        }).then(response => response.json());
    }
};

// Hook into the UI to replace demo functionality with real API calls
document.addEventListener('DOMContentLoaded', function() {
    console.log('TextNow Max Creator - Real API Integration Loaded');
    
    // Hook into the Create Accounts form
    const startBtn = document.querySelector('#start-creation-btn');
    if (startBtn) {
        startBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const countInput = document.querySelector('input[name="count"]');
            const areaCodesInput = document.querySelector('input[name="area_codes"]');
            
            const count = countInput ? parseInt(countInput.value || "10") : 10;
            const areaCodes = areaCodesInput ? areaCodesInput.value : '';
            
            console.log(`Creating ${count} accounts with area codes: ${areaCodes}`);
            
            // Show loading spinner
            const statusDiv = document.querySelector('#creation-status');
            if (statusDiv) {
                statusDiv.innerHTML = 'Starting account creation...';
                statusDiv.style.display = 'block';
            }
            
            window.realAPI.createAccounts(count, areaCodes)
                .then(result => {
                    if (result.success) {
                        if (statusDiv) {
                            statusDiv.innerHTML = 'Account creation started! Check the logs for progress.';
                        } else {
                            alert('Account creation started! Check the logs for progress.');
                        }
                    } else {
                        if (statusDiv) {
                            statusDiv.innerHTML = 'Error: ' + result.error;
                        } else {
                            alert('Error: ' + result.error);
                        }
                    }
                })
                .catch(err => {
                    console.error('Error creating accounts:', err);
                    if (statusDiv) {
                        statusDiv.innerHTML = 'Error creating accounts. Check the console for details.';
                    } else {
                        alert('Error creating accounts. Check the console for details.');
                    }
                });
        });
    }
    
    // Replace IP rotation button
    const rotateIpBtn = document.querySelector('#rotate-ip-btn');
    if (rotateIpBtn) {
        rotateIpBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            console.log('Rotating IP address...');
            
            const statusSpan = document.querySelector('#ip-status');
            if (statusSpan) {
                statusSpan.textContent = 'Rotating...';
            }
            
            window.realAPI.rotateIP()
                .then(result => {
                    if (result.success) {
                        if (statusSpan) {
                            statusSpan.textContent = `Rotated! New IP: ${result.new_ip}`;
                        } else {
                            alert(`IP rotated successfully! Old: ${result.old_ip}, New: ${result.new_ip}`);
                        }
                    } else {
                        if (statusSpan) {
                            statusSpan.textContent = `Error: ${result.error}`;
                        } else {
                            alert('Error: ' + result.error);
                        }
                    }
                })
                .catch(err => {
                    console.error('Error rotating IP:', err);
                    if (statusSpan) {
                        statusSpan.textContent = 'Error rotating IP';
                    } else {
                        alert('Error rotating IP. Check the console for details.');
                    }
                });
        });
    }
    
    // Add real functionality to all buttons with data-real-action attribute
    document.querySelectorAll('[data-real-action]').forEach(element => {
        element.addEventListener('click', function(e) {
            e.preventDefault();
            
            const action = this.getAttribute('data-real-action');
            const params = JSON.parse(this.getAttribute('data-params') || '{}');
            
            console.log(`Executing real action: ${action}`, params);
            
            switch (action) {
                case 'create-accounts':
                    window.realAPI.createAccounts(params.count || 1, params.areaCodes || '');
                    break;
                    
                case 'rotate-ip':
                    window.realAPI.rotateIP();
                    break;
                    
                case 'send-message':
                    window.realAPI.sendMessage(params.accountId, params.recipient, params.message);
                    break;
                    
                default:
                    console.warn(`Unknown real action: ${action}`);
            }
        });
    });
});