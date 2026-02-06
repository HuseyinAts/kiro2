// KIRO2 Claude Auto-Router - Content Script
// Intercepts prompts and adds routing

let orchestratorEndpoint = 'http://localhost:8765/orchestrate';

// Find Claude's input field
function findInputField() {
    // Claude.ai uses various selectors, try common ones
    const selectors = [
        'textarea[placeholder*="Message"]',
        'textarea[placeholder*="Ask"]',
        'div[contenteditable="true"]',
        '.composer-textarea',
        '#prompt-input'
    ];
    
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) return element;
    }
    return null;
}

// Intercept form submission
function interceptSubmit() {
    const inputField = findInputField();
    if (!inputField) {
        console.log('Claude input field not found');
        return;
    }
    
    // Listen for Enter key or submit button
    inputField.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            const prompt = inputField.value || inputField.textContent;
            
            if (prompt && prompt.trim()) {
                // Get routing decision
                const routing = await getRouting(prompt);
                
                if (routing && routing.agent !== 'general-purpose') {
                    // Modify prompt with routing
                    const modifiedPrompt = `Use Task tool with subagent_type='${routing.agent}' to: ${prompt}`;
                    
                    // Update input field
                    if (inputField.value !== undefined) {
                        inputField.value = modifiedPrompt;
                    } else {
                        inputField.textContent = modifiedPrompt;
                    }
                    
                    // Show visual feedback
                    showRoutingFeedback(routing);
                }
            }
        }
    });
}

// Get routing from orchestrator
async function getRouting(prompt) {
    try {
        const response = await fetch(orchestratorEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                auto_execute: false
            })
        });
        
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.error('Routing error:', error);
    }
    return null;
}

// Show visual feedback
function showRoutingFeedback(routing) {
    // Create or update feedback element
    let feedback = document.getElementById('kiro2-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.id = 'kiro2-feedback';
        feedback.className = 'kiro2-routing-feedback';
        document.body.appendChild(feedback);
    }
    
    feedback.innerHTML = `
        <div class="kiro2-header">🤖 Auto-Routing Active</div>
        <div class="kiro2-agent">Agent: ${routing.agent}</div>
        <div class="kiro2-confidence">Confidence: ${Math.round(routing.confidence * 100)}%</div>
    `;
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        feedback.style.opacity = '0';
        setTimeout(() => {
            feedback.style.display = 'none';
        }, 300);
    }, 3000);
    
    // Show feedback
    feedback.style.display = 'block';
    feedback.style.opacity = '1';
}

// Initialize when page loads
function initialize() {
    console.log('KIRO2 Auto-Router: Initializing...');
    
    // Wait for Claude interface to load
    const checkInterval = setInterval(() => {
        if (findInputField()) {
            clearInterval(checkInterval);
            interceptSubmit();
            console.log('KIRO2 Auto-Router: Ready!');
        }
    }, 1000);
}

// Start
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}