// Global variables
let sessionId = null;

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    const tokenForm = document.getElementById('tokenForm');
    const continueSessionBtn = document.getElementById('continueSessionBtn');
    const newTokensBtn = document.getElementById('newTokensBtn');
    const existingSessionId = document.getElementById('existingSessionId');
    
    if (tokenForm) {
        tokenForm.addEventListener('submit', handleTokenValidation);
    }
    
    if (continueSessionBtn && existingSessionId) {
        continueSessionBtn.addEventListener('click', () => {
            sessionId = existingSessionId.value;
            loadObjectSelection();
        });
    }
    
    if (newTokensBtn) {
        newTokensBtn.addEventListener('click', () => {
            document.querySelector('.existing-session').style.display = 'none';
            document.getElementById('tokenSection').style.display = 'block';
            sessionId = null;
        });
    }
    
    // Check if we have a session ID from existing session
    if (existingSessionId && existingSessionId.value) {
        sessionId = existingSessionId.value;
    }
}

async function handleTokenValidation(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const submitBtn = document.getElementById('validateBtn');
    const statusDiv = document.getElementById('authStatus');
    const loadingDiv = document.getElementById('loadingIndicator');
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.textContent = 'Validating...';
    loadingDiv.style.display = 'block';
    statusDiv.style.display = 'none';
    
    try {
        const response = await fetch('/validate-tokens', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            sessionId = result.session_id;
            showStatus('Tokens validated successfully! Loading available objects...', 'success');
            await loadObjectSelection();
        } else {
            throw new Error(result.detail || 'Token validation failed');
        }
    } catch (error) {
        console.error('Validation error:', error);
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Validate Tokens';
        loadingDiv.style.display = 'none';
    }
}

async function loadObjectSelection() {
    if (!sessionId) {
        showStatus('No valid session found', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/objects/${sessionId}`);
        const result = await response.json();
        
        if (response.ok) {
            displayObjectSelection(result);
        } else {
            throw new Error(result.detail || 'Failed to load objects');
        }
    } catch (error) {
        console.error('Object loading error:', error);
        showStatus(`Error loading objects: ${error.message}`, 'error');
    }
}

function displayObjectSelection(data) {
    const objectSection = document.getElementById('objectSelection');
    const standardObjectsDiv = document.getElementById('standardObjects');
    const customObjectsDiv = document.getElementById('customObjects');
    
    // Clear existing content
    standardObjectsDiv.innerHTML = '';
    customObjectsDiv.innerHTML = '';
    
    // Standard objects
    const standardObjects = ['contacts', 'companies', 'deals', 'tickets', 'products', 'line_items'];
    standardObjects.forEach(objectType => {
        const objectCard = createObjectCard(objectType, formatObjectName(objectType));
        standardObjectsDiv.appendChild(objectCard);
    });
    
    // Custom objects from Portal A
    if (data.portal_a && data.portal_a.custom) {
        data.portal_a.custom.forEach(obj => {
            const objectCard = createObjectCard(obj.name, obj.labels?.plural || obj.name, true);
            customObjectsDiv.appendChild(objectCard);
        });
    }
    
    // Show the object selection section
    objectSection.style.display = 'block';
    
    // Hide auth status after successful validation
    setTimeout(() => {
        const statusDiv = document.getElementById('authStatus');
        statusDiv.style.display = 'none';
    }, 3000);
}

function createObjectCard(objectType, displayName, isCustom = false) {
    const card = document.createElement('a');
    card.href = '#';
    card.className = 'object-card';
    card.innerHTML = `
        <div>
            ${isCustom ? '🔧' : '📋'} ${displayName}
        </div>
    `;
    
    card.addEventListener('click', (e) => {
        e.preventDefault();
        navigateToComparison(objectType);
    });
    
    return card;
}

async function navigateToComparison(objectType) {
    if (!sessionId) {
        showStatus('No valid session found', 'error');
        return;
    }
    
    const loadingDiv = document.getElementById('loadingIndicator');
    loadingDiv.style.display = 'block';
    
    try {
        // Navigate to comparison page
        window.location.href = `/compare/${sessionId}/${objectType}`;
    } catch (error) {
        console.error('Navigation error:', error);
        showStatus(`Error: ${error.message}`, 'error');
        loadingDiv.style.display = 'none';
    }
}

function formatObjectName(objectType) {
    const nameMap = {
        'contacts': 'Contacts',
        'companies': 'Companies',
        'deals': 'Deals',
        'tickets': 'Tickets',
        'products': 'Products',
        'line_items': 'Line Items',
        'quotes': 'Quotes',
        'calls': 'Calls',
        'emails': 'Emails',
        'meetings': 'Meetings',
        'notes': 'Notes',
        'tasks': 'Tasks'
    };
    return nameMap[objectType] || objectType.charAt(0).toUpperCase() + objectType.slice(1);
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('authStatus');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
    statusDiv.style.display = 'block';
}

// Utility functions for API calls
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Export functions for use in other scripts
window.HubSpotCompareApp = {
    sessionId: () => sessionId,
    apiCall,
    showStatus,
    formatObjectName
};