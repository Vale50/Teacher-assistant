// Share Lesson Plan Function
async function shareLessonPlan(lessonId) {
    if (!lessonId) {
        alert('No lesson plan ID found');
        return;
    }
    
    const token = getAuthToken();
    if (!token) {
        alert('Please login to share lesson plans');
        return;
    }
    
    // Show loading modal
    showShareModal('loading');
    
    try {
        const response = await fetch(`https://seashell-app-onfk3.ondigitalocean.app/api/publish-lesson-plan/${lessonId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Show success modal with share link
        showShareModal('success', data.public_url);
        
    } catch (error) {
        console.error('Error sharing lesson plan:', error);
        showShareModal('error', null, error.message);
    }
}

// Show Share Modal
function showShareModal(state, shareUrl = null, errorMessage = null) {
    // Remove existing modal if any
    const existingModal = document.getElementById('share-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    let modalContent = '';
    
    if (state === 'loading') {
        modalContent = `
            <div class="modal-content">
                <h3>🔄 Publishing Lesson...</h3>
                <div class="spinner"></div>
                <p>Generating shareable link...</p>
            </div>
        `;
    } else if (state === 'success') {
        modalContent = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>✅ Lesson Published!</h3>
                    <button class="close-modal" onclick="closeShareModal()">×</button>
                </div>
                <div class="modal-body">
                    <p>Your lesson has been published successfully. Share this link with your students:</p>
                    
                    <div class="share-link-container">
                        <input type="text" id="share-link-input" value="${shareUrl}" readonly>
                        <button onclick="copyShareLink('${shareUrl}')" class="copy-btn">
                            📋 Copy Link
                        </button>
                    </div>
                    
                    <div class="share-options">
                        <h4>Share via:</h4>
                        <div class="share-buttons">
                            <button onclick="shareViaEmail('${shareUrl}')" class="share-option-btn">
                                📧 Email
                            </button>
                            <button onclick="openShareLink('${shareUrl}')" class="share-option-btn">
                                🔗 Open Link
                            </button>
                            <button onclick="generateQRCode('${shareUrl}')" class="share-option-btn">
                                📱 QR Code
                            </button>
                        </div>
                    </div>
                    
                    <div class="share-info">
                        <p><strong>Note:</strong> Anyone with this link can view the lesson plan. The link will remain active until you unpublish it.</p>
                    </div>
                </div>
            </div>
        `;
    } else if (state === 'error') {
        modalContent = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>❌ Publishing Failed</h3>
                    <button class="close-modal" onclick="closeShareModal()">×</button>
                </div>
                <div class="modal-body">
                    <p class="error-message">${errorMessage || 'Failed to publish lesson plan. Please try again.'}</p>
                    <button onclick="closeShareModal()" class="retry-btn">Close</button>
                </div>
            </div>
        `;
    }
    
    const modal = document.createElement('div');
    modal.id = 'share-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = modalContent;
    
    document.body.appendChild(modal);
    
    // Animate in
    setTimeout(() => {
        modal.classList.add('active');
    }, 10);
}

// Close Share Modal
function closeShareModal() {
    const modal = document.getElementById('share-modal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

// Copy Share Link
async function copyShareLink(url) {
    try {
        await navigator.clipboard.writeText(url);
        
        // Show success feedback
        const copyBtn = document.querySelector('.copy-btn');
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '✅ Copied!';
        copyBtn.style.background = '#2ecc71';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '';
        }, 2000);
        
    } catch (error) {
        console.error('Failed to copy:', error);
        
        // Fallback: select text
        const input = document.getElementById('share-link-input');
        input.select();
        document.execCommand('copy');
        
        alert('Link copied to clipboard!');
    }
}

// Share via Email
function shareViaEmail(url) {
    const subject = encodeURIComponent('Math Lesson Plan');
    const body = encodeURIComponent(`Check out this lesson plan: ${url}`);
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
}

// Open Share Link
function openShareLink(url) {
    window.open(url, '_blank');
}

// Generate QR Code
function generateQRCode(url) {
    // Use a free QR code API
    const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(url)}`;
    
    const qrModal = document.createElement('div');
    qrModal.className = 'qr-modal-overlay';
    qrModal.innerHTML = `
        <div class="qr-modal-content">
            <div class="modal-header">
                <h3>📱 QR Code</h3>
                <button class="close-modal" onclick="this.closest('.qr-modal-overlay').remove()">×</button>
            </div>
            <div class="qr-body">
                <img src="${qrCodeUrl}" alt="QR Code" style="max-width: 300px; margin: 20px auto; display: block;">
                <p>Students can scan this QR code to access the lesson</p>
                <a href="${qrCodeUrl}" download="lesson-qr-code.png" class="download-qr-btn">
                    💾 Download QR Code
                </a>
            </div>
        </div>
    `;
    
    document.body.appendChild(qrModal);
    
    setTimeout(() => {
        qrModal.classList.add('active');
    }, 10);
}