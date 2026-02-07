// Improved toggleExplanations function
function toggleExplanations() {
    console.log("Toggle explanations called");
    
    // Find the explanations container
    const explanations = document.getElementById('explanations');
    const button = document.querySelector('.show-explanations-btn');
    
    // Check if elements exist
    if (!explanations) {
      console.error("Explanations container not found");
      
      // Try to handle redirection to explanation page
      const quizId = getQuizIdFromUrl();
      const studentName = window.studentName || 'Anonymous';
      
      if (quizId) {
        console.log("Redirecting to explanation page");
        
        // Show loading overlay
        document.body.insertAdjacentHTML('beforeend', `
          <div id="redirect-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
               background-color: rgba(0, 0, 0, 0.5); display: flex; justify-content: center; 
               align-items: center; z-index: 9999; backdrop-filter: blur(3px);">
            <div style="background-color: white; padding: 30px; border-radius: 10px; text-align: center; max-width: 500px;">
              <div style="width: 50px; height: 50px; border: 5px solid #f3f3f3; border-top: 5px solid #6C63FF; 
                   border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
              <h3 style="margin-bottom: 10px; color: #333;">Loading Explanations</h3>
              <p style="margin-bottom: 5px; color: #666;">Redirecting to detailed explanations...</p>
            </div>
          </div>
        `);
        
        // Redirect to explanation page with available data
        setTimeout(() => {
          window.location.href = `explanation.html?id=${quizId}&student=${encodeURIComponent(studentName)}`;
        }, 1000);
      } else {
        alert("Cannot show explanations - please submit the quiz first.");
      }
      return;
    }
    
    // Toggle visibility if elements exist
    if (!button) {
      console.warn("Show explanations button not found");
      // Just toggle the explanations without updating button
      explanations.style.display = explanations.style.display === 'block' ? 'none' : 'block';
    } else {
      if (explanations.style.display === 'block') {
        explanations.style.display = 'none';
        button.innerHTML = '<i class="fas fa-info-circle"></i> Show Corrections';
      } else {
        explanations.style.display = 'block';
        button.innerHTML = '<i class="fas fa-times-circle"></i> Hide Corrections';
        
        // Scroll to explanations
        setTimeout(() => {
          explanations.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
      }
    }
  }

  // Add this to your code to handle server errors
function handleServerError() {
    const quizContent = document.getElementById('quiz-content');
    if (!quizContent) return;
    
    quizContent.innerHTML = `
      <div style="background-color: white; padding: 30px; border-radius: 10px; text-align: center; margin: 20px auto; max-width: 600px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="color: #333; margin-bottom: 15px;">Quiz Loading Error</h2>
        <p style="color: #666; margin-bottom: 20px;">We're having trouble loading the quiz from the server. You can try one of the following options:</p>
        
        <div style="display: flex; flex-direction: column; gap: 10px;">
          <button onclick="window.location.reload()" style="background: #6C63FF; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: 500;">
            <i class="fas fa-redo"></i> Reload Quiz
          </button>
          
          <button onclick="redirectToExplanation()" style="background: #10B981; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: 500;">
            <i class="fas fa-info-circle"></i> View Explanations
          </button>
        </div>
      </div>
    `;
  }
  
  // Function to redirect to explanation page
  function redirectToExplanation() {
    const quizId = getQuizIdFromUrl();
    const studentName = window.studentName || 'Anonymous';
    
    if (quizId) {
      window.location.href = `explanation.html?id=${quizId}&student=${encodeURIComponent(studentName)}`;
    } else {
      alert("Cannot load explanations without a quiz ID.");
    }
  }
  
  // Modify your loadQuiz function to include error handling
  const originalLoadQuiz = window.loadQuiz;
  window.loadQuiz = function() {
    try {
      // Call original function
      originalLoadQuiz.apply(this, arguments);
    } catch (error) {
      console.error("Error in loadQuiz:", error);
      handleServerError();
    }
  };

  // Self-contained emergency fix for quiz loading and explanation access
(function() {
    // Use a unique namespace to avoid conflicts
    const EmergencyFix = {
      init: function() {
        console.log("Initializing emergency quiz fix");
        this.setupEventListeners();
        this.handleUrlParameters();
      },
  
      setupEventListeners: function() {
        // Fix explanation button clicks
        document.addEventListener('click', function(e) {
          if (e.target.matches('.show-explanations-btn, #forced-explanations-btn') || 
              e.target.closest('.show-explanations-btn, #forced-explanations-btn')) {
            e.preventDefault();
            console.log("Explanation button click intercepted");
            EmergencyFix.redirectToExplanation();
          }
        }, true);
        
        // Fix quiz submit button clicks if needed
        document.addEventListener('click', function(e) {
          if (e.target.matches('.submit-button') || e.target.closest('.submit-button')) {
            // Only intercept if the original function is failing
            try {
              if (typeof submitQuiz !== 'function') {
                e.preventDefault();
                console.log("Submit button click intercepted due to missing function");
                EmergencyFix.redirectToExplanation();
              }
            } catch (error) {
              e.preventDefault();
              console.log("Submit button click intercepted due to error", error);
              EmergencyFix.redirectToExplanation();
            }
          }
        }, true);
      },
  
      handleUrlParameters: function() {
        // Get student name from URL if present
        const urlParams = new URLSearchParams(window.location.search);
        const studentParam = urlParams.get('student');
        
        if (studentParam && studentParam.trim() !== '') {
          console.log("Student name found in URL:", studentParam);
          window.studentName = decodeURIComponent(studentParam);
          
          // Add a small delay to ensure DOM is ready
          setTimeout(() => {
            // Hide student modal
            const studentModal = document.getElementById('studentNameModal');
            if (studentModal) {
              studentModal.style.display = 'none';
            }
            
            // Show quiz header
            const quizHeader = document.getElementById('quizHeader');
            if (quizHeader) {
              quizHeader.style.display = 'flex';
            }
            
            // Update student welcome
            const welcomeEl = document.getElementById('studentWelcome');
            if (welcomeEl) {
              welcomeEl.textContent = `Welcome, ${window.studentName}!`;
            }
            
            // Check if we need to force explanations
            if (urlParams.get('showExplanations') === 'true') {
              this.redirectToExplanation();
            }
          }, 500);
        }
      },
  
      getQuizIdFromUrl: function() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('id') || '';
      },
  
      redirectToExplanation: function() {
        const quizId = this.getQuizIdFromUrl();
        const studentName = window.studentName || 'Anonymous';
        
        if (quizId) {
          console.log("Redirecting to explanation page");
          
          // Show loading overlay
          const existingOverlay = document.getElementById('redirect-overlay');
          if (!existingOverlay) {
            document.body.insertAdjacentHTML('beforeend', `
              <div id="redirect-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                   background-color: rgba(0, 0, 0, 0.5); display: flex; justify-content: center; 
                   align-items: center; z-index: 9999; backdrop-filter: blur(3px);">
                <div style="background-color: white; padding: 30px; border-radius: 10px; text-align: center; max-width: 500px;">
                  <div style="width: 50px; height: 50px; border: 5px solid #f3f3f3; border-top: 5px solid #6C63FF; 
                       border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
                  <h3 style="margin-bottom: 10px; color: #333;">Loading Explanations</h3>
                  <p style="margin-bottom: 5px; color: #666;">Redirecting to detailed explanations...</p>
                </div>
              </div>
            `);
          }
          
          // Make function available globally without conflicts
          window.emergencyRedirectToExplanation = function() {
            EmergencyFix.redirectToExplanation();
          };
          
          // Redirect to explanation page
          setTimeout(() => {
            window.location.href = `explanation.html?id=${quizId}&student=${encodeURIComponent(studentName)}`;
          }, 1000);
        } else {
          alert("Cannot load explanations without a quiz ID.");
        }
      }
    };
  
    // Initialize the fix when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        EmergencyFix.init();
      });
    } else {
      EmergencyFix.init();
    }
    
    // Make emergency functions available to window with unique names
    window.emergencyRedirectToExplanation = function() {
      EmergencyFix.redirectToExplanation();
    };
  })();