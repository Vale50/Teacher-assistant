// Add the missing config object
const config = {
    // API endpoint
    apiEndpoint: window.location.origin || 'https://seashell-app-onfk3.ondigitalocean.app',
    
    // Helper to check if we're on the flashcard page
    isFlashcardPage: function() {
      return window.location.pathname.includes('flashcards.html') || 
             document.getElementById('flashcard-preview') !== null;
    },
    
    // Helper to check if we're on the quiz page
    isQuizPage: function() {
      return window.location.pathname.includes('quiz.html') || 
             document.querySelector('.quiz-container') !== null;
    }
  };
  
  // Add the missing enhanceFlashcardPage f.unction
  function enhanceFlashcardPage() {
    console.log("Enhancing flashcard page...");
    // Implementation will depend on specific requirements
    // This is a placeholder implementation
  }
  
  // Add the missing enhanceQuizPage function
  function enhanceQuizPage() {
    console.log("Enhancing quiz page...");
    // Implementation will depend on specific requirements
    // This is a placeholder implementation
  }
  
  // Add the missing enhanceQuizRedirect function
  function enhanceQuizRedirect() {
    console.log("Enhancing quiz redirect functionality...");
    // Implementation will depend on specific requirements
    // This is a placeholder implementation
  }
  
  /**
   * Enhanced Flashcard Creator with Quiz Generation
   * 
   * This script adds quiz generation functionality to the flashcard creator.
   * Features:
   * - Automatic quiz generation from flashcards
   * - Customizable quiz settings (question count, time limit, question type)
   * - Quiz preview display 
   * - Ability to edit, regenerate, and save quiz questions
   */
  
  // Function to get quiz options from the form
  // Error handling utilities
  const ErrorHandler = {
      // Show formatted error message
      showError: function(message) {
          const errorDiv = document.getElementById('error-message');
          if (!errorDiv) {
              // Create error div if it doesn't exist
              const newErrorDiv = document.createElement('div');
              newErrorDiv.id = 'error-message';
              newErrorDiv.className = 'error-message';
              
              // Find a good place to add it
              const container = document.querySelector('.container');
              if (container) {
                  container.prepend(newErrorDiv);
              } else {
                  document.body.prepend(newErrorDiv);
              }
          }
          
          const errorDiv2 = document.getElementById('error-message');
          if (errorDiv2) {
              errorDiv2.textContent = message;
              errorDiv2.style.display = 'block';
              
              // Add some scroll if needed
              if (errorDiv2.getBoundingClientRect().top < 0) {
                  errorDiv2.scrollIntoView({ behavior: 'smooth' });
              }
          } else {
              // Fallback to alert if we can't create or find error div
              alert(message);
          }
      },
      
      // Show authentication error (without auto logout)
      showAuthError: function() {
          this.showError(
              'Authentication error occurred. Your session may be expired, but you can try again. If problems persist, you may need to log in again.'
          );
      }
  };
 
  // Function to add quiz options UI to the form
  function addQuizOptionsUI() {
      // Find the flashcard parameters form group
      const parametersSection = document.querySelector('.form-group h2')?.closest('.form-group');
      if (!parametersSection) {
          console.warn("Could not find parameters section to add quiz options");
          return;
      }
      
      // Create quiz options form group
      const quizOptionsGroup = document.createElement('div');
      quizOptionsGroup.className = 'form-group';
      quizOptionsGroup.innerHTML = `
          <h2>Quiz Options</h2>
          <div style="margin-bottom: 15px;">
              <input type="checkbox" id="auto-generate-quiz" checked>
              <label for="auto-generate-quiz" style="display: inline; margin-left: 8px; font-weight: normal;">
                  Automatically generate a quiz from flashcards
              </label>
          </div>
          
          <div id="quiz-options-container" style="padding: 15px; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
              <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 15px;">
                  <div style="flex: 1; min-width: 200px;">
                      <label for="quiz-question-count">Number of Questions:</label>
                      <input type="number" id="quiz-question-count" min="3" max="20" value="10" style="width: 100%; padding: 8px; border: 1px solid #e2e8f0; border-radius: 4px;">
                  </div>
                  
                  <div style="flex: 1; min-width: 200px;">
                      <label for="quiz-time-limit">Time Limit (minutes):</label>
                      <input type="number" id="quiz-time-limit" min="5" max="120" value="30" style="width: 100%; padding: 8px; border: 1px solid #e2e8f0; border-radius: 4px;">
                  </div>
              </div>
              
              <div style="margin-bottom: 15px;">
                  <label style="display: block; margin-bottom: 10px;">Question Type:</label>
                  <div style="display: flex; flex-wrap: wrap; gap: 15px;">
                      <div style="display: flex; align-items: center;">
                          <input type="radio" name="quiz-question-type" id="quiz-type-multiple-choice" value="multiple_choice" checked>
                          <label for="quiz-type-multiple-choice" style="margin-left: 8px; font-weight: normal;">Multiple Choice</label>
                      </div>
                      <div style="display: flex; align-items: center;">
                          <input type="radio" name="quiz-question-type" id="quiz-type-true-false" value="true_false">
                          <label for="quiz-type-true-false" style="margin-left: 8px; font-weight: normal;">True/False</label>
                      </div>
                  </div>
              </div>
              
              <div>
                  <label style="display: block; margin-bottom: 10px;">Quiz Mode:</label>
                  <div style="display: flex; flex-wrap: wrap; gap: 15px;">
                      <div style="display: flex; align-items: center;">
                          <input type="radio" name="quiz-mode" id="quiz-mode-list" value="list" checked>
                          <label for="quiz-mode-list" style="margin-left: 8px; font-weight: normal;">List View (All questions at once)</label>
                      </div>
                      <div style="display: flex; align-items: center;">
                          <input type="radio" name="quiz-mode" id="quiz-mode-auto" value="auto">
                          <label for="quiz-mode-auto" style="margin-left: 8px; font-weight: normal;">Auto Mode (One question at a time)</label>
                      </div>
                  </div>
              </div>
          </div>
      `;
      
      // Insert after parameters section
      parametersSection.parentNode.insertBefore(quizOptionsGroup, parametersSection.nextSibling);
      
      // Add event listener to toggle options visibility
      const autoGenerateCheckbox = document.getElementById('auto-generate-quiz');
      const optionsContainer = document.getElementById('quiz-options-container');
      
      if (autoGenerateCheckbox && optionsContainer) {
          autoGenerateCheckbox.addEventListener('change', function() {
              optionsContainer.style.display = this.checked ? 'block' : 'none';
          });
      }
  }
   
  // Quiz Manager for handling quiz generation and display
  const QuizManager = {
      quizData: null,
      
      // Create quiz preview UI
      createQuizUI: function() {
          // Skip if it already exists
          if (document.getElementById('quiz-preview-container')) {
              return;
          }
          
          // Create container div
          const previewContainer = document.createElement('div');
          previewContainer.id = 'quiz-preview-container';
          previewContainer.className = 'form-group';
          previewContainer.style.display = 'none';
          previewContainer.style.marginTop = '30px';
          
          // Create HTML content
          previewContainer.innerHTML = `
              <h2>Quiz Preview</h2>
              <p>This quiz will be available to students after completing the flashcards.</p>
              
              <div id="quiz-questions-container" class="quiz-preview-content">
                  <div class="loading" style="text-align: center; padding: 20px;">
                      Generating quiz preview...
                  </div>
              </div>
              
              <div class="quiz-preview-actions">
                  <button id="regenerate-quiz-btn" class="edit-btn regenerate-btn">
                      <i class="fas fa-sync-alt"></i> Regenerate Quiz
                  </button>
                  <button id="edit-quiz-btn" class="edit-btn">
                      <i class="fas fa-edit"></i> Edit Questions
                  </button>
                  <button id="save-quiz-btn" class="edit-btn save-btn">
                      <i class="fas fa-save"></i> Save Changes
                  </button>
              </div>
          `;
          
          // Find appropriate location to add the preview container
          // Try to add it after the flashcard preview
          const flashcardPreview = document.getElementById('flashcard-preview');
          if (flashcardPreview) {
              flashcardPreview.parentNode.insertBefore(previewContainer, flashcardPreview.nextSibling);
          } else {
              // Fallback: Append to the container
              const container = document.querySelector('.container');
              if (container) {
                  container.appendChild(previewContainer);
              }
          }
          
          // Set up event listeners
          document.getElementById('regenerate-quiz-btn').addEventListener('click', () => this.generateQuiz(window.flashcardSetId));
          document.getElementById('edit-quiz-btn').addEventListener('click', () => this.enableEditing());
          document.getElementById('save-quiz-btn').addEventListener('click', () => this.saveChanges());
          
          console.log("Quiz preview UI created successfully");
      },
      
      // Enable editing of questions
      enableEditing: function() {
          if (!this.quizData) {
              alert("No quiz data available to edit");
              return;
          }
          
          // Find all editable elements
          const editables = document.querySelectorAll('.editable');
          
          // Make them editable and add styling
          editables.forEach(element => {
              element.contentEditable = true;
              element.classList.add('editing');
              element.style.backgroundColor = '#f0f9ff';
              element.style.padding = '2px 5px';
              element.style.borderRadius = '3px';
              element.style.border = '1px dashed #4299e1';
          });
          
          // Add instruction message
          const container = document.getElementById('quiz-questions-container');
          if (container) {
              const instructionDiv = document.createElement('div');
              instructionDiv.id = 'editing-instructions';
              instructionDiv.style.padding = '10px';
              instructionDiv.style.backgroundColor = '#e6fffb';
              instructionDiv.style.borderRadius = '8px';
              instructionDiv.style.marginBottom = '15px';
              instructionDiv.style.borderLeft = '4px solid #0d9488';
              instructionDiv.innerHTML = `
                  <div style="display: flex; align-items: center; gap: 10px;">
                      <div style="font-size: 18px;">✏️</div>
                      <div>
                          <strong>Editing Mode Enabled</strong>
                          <div>Click on any question text or option to edit. Click "Save Changes" when done.</div>
                      </div>
                  </div>
              `;
              
              container.insertBefore(instructionDiv, container.firstChild);
          }
          
          // Change the edit button to say "Cancel Editing"
          const editButton = document.getElementById('edit-quiz-btn');
          if (editButton) {
              editButton.innerHTML = '<i class="fas fa-times"></i> Cancel Editing';
              editButton.removeEventListener('click', () => this.enableEditing());
              editButton.addEventListener('click', () => this.cancelEditing());
          }
      },
      
      // Cancel editing without saving
      cancelEditing: function() {
          // Remove editing styles
          const editables = document.querySelectorAll('.editable');
          editables.forEach(element => {
              element.contentEditable = false;
              element.classList.remove('editing');
              element.style.backgroundColor = '';
              element.style.padding = '';
              element.style.borderRadius = '';
              element.style.border = '';
          });
          
          // Remove instruction message
          const instructions = document.getElementById('editing-instructions');
          if (instructions) {
              instructions.remove();
          }
          
          // Change the button back
          const editButton = document.getElementById('edit-quiz-btn');
          if (editButton) {
              editButton.innerHTML = '<i class="fas fa-edit"></i> Edit Questions';
              editButton.removeEventListener('click', () => this.cancelEditing());
              editButton.addEventListener('click', () => this.enableEditing());
          }
          
          // Refresh the display with original data
          this.displayQuiz(this.quizData);
      },
      
      // Display quiz preview
      displayQuiz: function(quizData) {
          const container = document.getElementById('quiz-questions-container');
          if (!container) {
              console.error("Quiz questions container not found");
              return;
          }
          
          // Store the quiz data for later use
          this.quizData = quizData;
          
          // Show the container
          document.getElementById('quiz-preview-container').style.display = 'block';
          
          // Generate HTML for questions
          let html = '';
          
          if (!quizData || !quizData.questions || quizData.questions.length === 0) {
              html = '<div class="error-message">No questions available for preview</div>';
          } else {
              html = `
                  <div class="quiz-meta" style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                      <div><strong>Quiz Title:</strong> ${quizData.title || 'Untitled Quiz'}</div>
                      <div><strong>Topic:</strong> ${quizData.topic || 'General'}</div>
                      <div><strong>Number of Questions:</strong> ${quizData.questions.length}</div>
                      <div><strong>Time Limit:</strong> ${quizData.time_limit || 30} minutes</div>
                  </div>
                  
                  <div class="quiz-questions">
              `;
              
              quizData.questions.forEach((question, index) => {
                  html += `
                      <div class="question-item" data-question-index="${index}">
                          <div class="question-text" style="margin-bottom: 10px; font-weight: 600;">
                              <span class="question-number" style="background: var(--primary-color, #00bfff); color: white; display: inline-block; width: 24px; height: 24px; line-height: 24px; text-align: center; border-radius: 50%; margin-right: 8px;">${index + 1}</span>
                              <span class="question-content editable" data-field="text">${question.text}</span>
                          </div>
                          
                          <div class="question-options">
                  `;
                  
                  // Handle different question types
                  if (question.type === 'multiple_choice' || question.type === 'true_false') {
                      question.options.forEach((option, optIndex) => {
                          const correctMark = option.isCorrect ? '✓' : '';
                          const optionStyle = option.isCorrect ? 'background-color: rgba(76, 175, 80, 0.1); border-color: #4CAF50;' : '';
                          
                          html += `
                              <div class="question-option" data-option-index="${optIndex}" style="display: flex; align-items: center; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; ${optionStyle}">
                                  <input type="radio" ${option.isCorrect ? 'checked' : ''} name="q${index}" disabled>
                                  <div style="margin-left: 10px; flex-grow: 1;">
                                      <span class="option-content editable" data-field="options[${optIndex}].text">${option.text}</span>
                                  </div>
                                  <div style="color: #4CAF50; font-weight: bold;">${correctMark}</div>
                              </div>
                          `;
                      });
                  } else if (question.type === 'paragraph') {
                      html += `
                          <div class="paragraph-area" style="padding: 10px; background: #f8f9fa; border: 1px solid #ddd; border-radius: 4px;">
                              <div style="font-style: italic; color: #666;">Open-ended question (student will provide written answer)</div>
                          </div>
                      `;
                  }
                  
                  html += `
                          </div>
                      </div>
                  `;
              });
              
              html += '</div>';
          }
          
          container.innerHTML = html;
          
          // Scroll to the quiz preview
          setTimeout(() => {
              document.getElementById('quiz-preview-container').scrollIntoView({ behavior: 'smooth' });
          }, 300);
      },
      
      // Save changes to quiz
      saveChanges: function() {
          if (!this.quizData) {
              alert("No quiz data available to save");
              return;
          }
          
          // Gather updated data from editable elements
          const editables = document.querySelectorAll('.editable');
          
          // Update quiz data with edited content
          editables.forEach(element => {
              const field = element.getAttribute('data-field');
              if (!field) return;
              
              // Handle option fields (options[0].text format)
              if (field.includes('options[')) {
                  const match = field.match(/options\[(\d+)\]\.text/);
                  if (match) {
                      const questionIndex = parseInt(element.closest('.question-item').getAttribute('data-question-index'));
                      const optionIndex = parseInt(match[1]);
                      
                      if (this.quizData.questions[questionIndex] && 
                          this.quizData.questions[questionIndex].options && 
                          this.quizData.questions[questionIndex].options[optionIndex]) {
                          this.quizData.questions[questionIndex].options[optionIndex].text = element.textContent;
                      }
                  }
              } 
              // Handle simple fields (text)
              else {
                  const questionIndex = parseInt(element.closest('.question-item').getAttribute('data-question-index'));
                  if (this.quizData.questions[questionIndex]) {
                      this.quizData.questions[questionIndex][field] = element.textContent;
                  }
              }
          });
          
          // Store updated quiz data
          if (this.quizData.flashcard_set_id) {
              try {
                  localStorage.setItem(`flashcard_quiz_${this.quizData.flashcard_set_id}`, JSON.stringify(this.quizData));
                  
                  // Also try to save to server
                  this.saveQuizToServer(this.quizData.flashcard_set_id, this.quizData)
                      .then(() => {
                          console.log("Saved quiz data to server");
                      })
                      .catch(error => {
                          console.warn("Failed to save quiz to server, but it's saved locally:", error);
                      });
              } catch (e) {
                  console.warn("Failed to store quiz data in localStorage:", e);
              }
          }
          
          // Remove editing styles
          editables.forEach(element => {
              element.contentEditable = false;
              element.classList.remove('editing');
              element.style.backgroundColor = '';
              element.style.padding = '';
              element.style.borderRadius = '';
              element.style.border = '';
          });
          
          // Remove instruction message
          const instructions = document.getElementById('editing-instructions');
          if (instructions) {
              instructions.remove();
          }
          
          // Change the button back
          const editButton = document.getElementById('edit-quiz-btn');
          if (editButton) {
              editButton.innerHTML = '<i class="fas fa-edit"></i> Edit Questions';
              editButton.removeEventListener('click', () => this.cancelEditing());
              editButton.addEventListener('click', () => this.enableEditing());
          }
          
          // Show success message
          const container = document.getElementById('quiz-questions-container');
          if (container) {
              const successDiv = document.createElement('div');
              successDiv.style.padding = '10px';
              successDiv.style.backgroundColor = '#d1fae5';
              successDiv.style.borderRadius = '8px';
              successDiv.style.marginBottom = '15px';
              successDiv.style.display = 'flex';
              successDiv.style.alignItems = 'center';
              successDiv.style.justifyContent = 'space-between';
              successDiv.innerHTML = `
                  <div style="display: flex; align-items: center; gap: 10px;">
                      <div style="font-size: 18px;">✅</div>
                      <div>
                          <strong>Changes Saved Successfully</strong>
                          <div>Your quiz changes have been saved and will be available to students.</div>
                      </div>
                  </div>
              `;
              
              container.insertBefore(successDiv, container.firstChild);
              
              // Remove success message after 3 seconds
              setTimeout(() => {
                  if (successDiv.parentNode) {
                      successDiv.parentNode.removeChild(successDiv);
                  }
              }, 3000);
          }
      },
      
      // Save quiz to server
      saveQuizToServer: function(setId, quizData) {
          return new Promise((resolve, reject) => {
              // Get token
              const token = TokenManager.getToken();
              if (!token) {
                  reject(new Error("No authentication token available"));
                  return;
              }
              
              // Make server request
              fetch(`/api/flashcard-set/${setId}/quiz`, {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/json',
                      'Authorization': `Bearer ${token}`
                  },
                  body: JSON.stringify({
                      quizData: quizData
                  })
              })
              .then(response => {
                  if (!response.ok) {
                      throw new Error(`Server returned ${response.status}`);
                  }
                  return response.json();
              })
              .then(data => {
                  resolve(data);
              })
              .catch(error => {
                  reject(error);
              });
          });
      },
      
      // Generate quiz from flashcards
      generateQuiz: function(setId) {
          if (!setId) {
              ErrorHandler.showError("No flashcard set available. Please generate flashcards first.");
              return;
          }
          
          // Make sure the UI is created
          if (!document.getElementById('quiz-preview-container')) {
              this.createQuizUI();
          }
          
          const container = document.getElementById('quiz-questions-container');
          if (container) {
              container.innerHTML = `
                  <div class="loading" style="text-align: center; padding: 20px;">
                      Generating quiz preview...
                  </div>
              `;
          }
          
          // Show the preview container
          const previewContainer = document.getElementById('quiz-preview-container');
          if (previewContainer) {
              previewContainer.style.display = 'block';
          }
          
          // Get quiz options
          const quizOptions = getQuizOptions();
          
          // Get flashcard data
          fetch(`/api/flashcard-set/${setId}`)
              .then(response => {
                  if (!response.ok) {
                      throw new Error(`Failed to load flashcard set (${response.status})`);
                  }
                  return response.json();
              })
              .then(data => {
                  if (!data.flashcards || data.flashcards.length === 0) {
                      throw new Error("No flashcards found to create quiz questions");
                  }
                  
                  // First try to see if a quiz already exists for this flashcard set
                  return fetch(`/api/flashcard-set/${setId}/quiz`)
                      .then(response => {
                          if (response.ok) {
                              return response.json();
                          } else if (response.status === 404) {
                              // No quiz exists yet, need to generate one
                              
                              // Generate quiz data on server using the generate-quiz endpoint
                              const requestData = {
                                  topic: data.flashcard_set.title || "Flashcard Quiz",
                                  grade_level: data.flashcard_set.grade_level || "all",
                                  numQuestions: quizOptions.questionCount || Math.min(10, data.flashcards.length), 
                                  types: [quizOptions.questionType || "multiple_choice"],
                                  mode: quizOptions.quizMode || "list",
                                  time_limit: quizOptions.timeLimit || 30,
                                  content_text: data.flashcards.map(card => `${card.front}: ${card.back}`).join("\n\n")
                              };
                              
                              return fetch('/api/generate-quiz', {
                                  method: 'POST',
                                  headers: {
                                      'Content-Type': 'application/json',
                                      'Authorization': `Bearer ${TokenManager.getToken()}`
                                  },
                                  body: JSON.stringify(requestData)
                              });
                          } else {
                              throw new Error(`Failed to check for existing quiz (${response.status})`);
                          }
                      });
              })
              .then(response => {
                  if (!response.ok) {
                      throw new Error(`Failed to generate quiz (${response.status})`);
                  }
                  return response.json();
              })
              .then(quizData => {
                  if (!quizData || (!quizData.quiz_data && !quizData.quiz_id)) {
                      throw new Error("Invalid quiz data received from server");
                  }
                  
                  // Get quiz data from response
                  const quiz = quizData.quiz_data || {};
                  quiz.flashcard_set_id = setId;
                  
                  // Store in localStorage for persistence
                  try {
                      localStorage.setItem(`flashcard_quiz_${setId}`, JSON.stringify(quiz));
                  } catch (e) {
                      console.warn("Failed to store quiz data in localStorage:", e);
                  }
                  
                  // Display the preview
                  this.displayQuiz(quiz);
                  
                  // Also try to save to server
                  this.saveQuizToServer(setId, quiz)
                  .catch(error => {
                      console.warn("Failed to save quiz to server, but it's saved locally:", error);
                  });
              })
              .catch(error => {
                  console.error("Error generating quiz:", error);
                  
                  // Show error in container
                  const container = document.getElementById('quiz-questions-container');
                  if (container) {
                      container.innerHTML = `
                          <div class="error-message" style="padding: 15px; background: #fee2e2; color: #b91c1c; border-radius: 8px;">
                              <h3>Error Generating Quiz</h3>
                              <p>${error.message}</p>
                              <button id="retry-quiz-btn" style="margin-top: 10px; padding: 8px 16px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                  Try Again
                              </button>
                          </div>
                      `;
                      
                      // Add event listener to retry button
                      document.getElementById('retry-quiz-btn').addEventListener('click', () => this.generateQuiz(setId));
                  }
              });
      }
  };

  // Expose QuizManager to window so other scripts can access it
  window.QuizManager = QuizManager;

  // Enhance the original generateFlashcards function to include quiz options
  function enhanceGenerateFlashcards() {
      // Store the original function
      const originalGenerateFlashcards = window.generateFlashcards;
      
      if (typeof originalGenerateFlashcards !== 'function') {
          console.error("Original generateFlashcards function not found");
          return;
      }
      
      // Replace with enhanced version
      window.generateFlashcards = function() {
          try {
              // Get form values as in the original function
              const gradeLevel = document.getElementById('grade-level').value;
              const numCards = document.getElementById('num-cards').value;
              const cardDifficulty = document.getElementById('card-difficulty').value;
              const timePerCard = document.getElementById('time-per-card').value;
            
            // Declare all variables at the beginning of the function
            let topic = '';
            let contentText = '';
            let sourceType = 'topic';
            let types = ['definition']; // Default flashcard types
            
            // Determine content source and set topic
            const activeTab = document.querySelector('.source-tab.active');
            const activeSourceTab = activeTab ? activeTab.getAttribute('data-source') : 'topic';
            
            // Get content based on selected source
            if (activeSourceTab === 'topic') {
                const topicInput = document.getElementById('topic-input');
                topic = topicInput ? topicInput.value.trim() : '';
                sourceType = 'topic';
                
                if (!topic) {
                    ErrorHandler.showError('Please enter a topic');
                    return;
                }
            } else if (activeSourceTab === 'text') {
                const textArea = document.getElementById('content-text');
                contentText = textArea ? textArea.value.trim() : '';
                topic = `Text-based flashcards: ${contentText.substring(0, 30)}${contentText.length > 30 ? '...' : ''}`;
                sourceType = 'text';
                
                if (!contentText) {
                    ErrorHandler.showError('Please enter some text content');
                    return;
                }
            } else if (activeSourceTab === 'file') {
                const fileInput = document.getElementById('content-file');
                if (!fileInput || !fileInput.files || !fileInput.files[0]) {
                    ErrorHandler.showError('Please upload a file');
                    return;
                }
                
                const file = fileInput.files[0];
                topic = `File-based flashcards: ${file.name}`;
                sourceType = 'file';
            }
            
            // Get authentication token
            const token = TokenManager.getToken();
            if (!token) {
                ErrorHandler.showError('Please login to generate flashcards');
                setLoadingState(false);
                showLoginOption();
                return;
            }
            
            // Get selected flashcard types
            try {
                const typeCheckboxes = document.querySelectorAll('.type-checkbox:checked');
                if (typeCheckboxes && typeCheckboxes.length > 0) {
                    types = Array.from(typeCheckboxes)
                        .map(cb => cb.value);
                }
            } catch (e) {
                console.error('Error getting flashcard types:', e);
            }
            
            // Get quiz generation preference
            const autoGenerateQuiz = document.getElementById('auto-generate-quiz')?.checked ?? true;
            
            // Get quiz options if available
            const quizOptions = getQuizOptions();
            
            // Prepare request data
            const requestData = {
                topic: topic,
                grade_level: gradeLevel,
                num_cards: parseInt(numCards),
                card_types: types,
                difficulty: cardDifficulty,
                time_per_card: parseInt(timePerCard),
                content_text: contentText,
                source_type: sourceType,
                auto_generate_quiz: autoGenerateQuiz,
                appearance_settings: window.flashcardColors || {}, // Add appearance settings if available
                quiz_options: quizOptions // Add quiz options
            };
            
            // Show loading state
            if (typeof setLoadingState === 'function') {
                setLoadingState(true);
            }
            
            // Call API
            fetch('/api/generate-flashcards', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(requestData),
                signal: (function() {
                    const controller = new AbortController();
                    setTimeout(() => controller.abort(), 20000);
                    return controller.signal;
                })() 
            })
            .then(response => {
                if (response.status === 401) {
                    throw new Error('Authentication failed. Please log in again.');
                } else if (response.status === 429) {
                    throw new Error('Too many requests. Please wait a moment before trying again.');
                } else if (response.status >= 500) {
                    throw new Error('The server is currently experiencing technical difficulties. Please try again later.');
                } else if (!response.ok) {
                    throw new Error(`Request failed with status: ${response.status}`);
                }
                
                return response.json();
            })
            .then(data => {
                console.log('Generated flashcards:', data);
                
                // Handle standard flashcard success
                if (typeof handleFlashcardSuccess === 'function') {
                    handleFlashcardSuccess(data);
                } else {
                    // Fallback handling if handleFlashcardSuccess is not defined
                    window.flashcardSetId = data.flashcard_set_id;
                    window.flashcards = data.flashcards;
                    
                    // Display flashcards (simple implementation)
                    const flashcardPreview = document.getElementById('flashcard-preview');
                    if (flashcardPreview) {
                        flashcardPreview.style.display = 'block';
                    }
                }
                
                // If auto-generate quiz is enabled and quiz data is available, display it
                if (autoGenerateQuiz) {
                    // Store the ID for later use
                    window.flashcardSetId = data.flashcard_set_id;
                    sessionStorage.setItem('current_flashcard_set_id', data.flashcard_set_id);
                    
                    // If the response includes quiz data, display it directly
                    if (data.quiz_data) {
                        // Create quiz preview UI if it doesn't exist
                        if (!document.getElementById('quiz-preview-container')) {
                            QuizManager.createQuizUI();
                        }
                        
                        // Display the quiz data
                        QuizManager.displayQuiz(data.quiz_data);
                    } else {
                        // Otherwise, generate quiz after a delay
                        setTimeout(() => {
                            if (!document.getElementById('quiz-preview-container')) {
                                QuizManager.createQuizUI();
                            }
                            QuizManager.generateQuiz(data.flashcard_set_id);
                        }, 1000);
                    }
                }
            })
            .catch(err => {
                console.error('Error generating flashcards:', err);
                
                // Provide a customized error message based on error type
                let errorMessage = err.message || 'Failed to generate flashcards. Please try again.';
                
                // For timeouts
                if (err.name === 'TimeoutError' || err.name === 'AbortError') {
                    errorMessage = 'Request timed out. The server may be overloaded. Please try again later.';
                }
                
                // For authentication errors
                if (err.message.includes('Authentication failed')) {
                    // Clear tokens as they're invalid
                    if (typeof TokenManager !== 'undefined' && typeof TokenManager.clearToken === 'function') {
                        TokenManager.clearToken();
                    }
                    
                    if (typeof ErrorHandler !== 'undefined' && typeof ErrorHandler.showAuthError === 'function') {
                        ErrorHandler.showAuthError();
                    } else {
                        // Fallback error handling
                        alert('Authentication failed. Please log in again.');
                    }
                } else {
                    if (typeof ErrorHandler !== 'undefined' && typeof ErrorHandler.showError === 'function') {
                        ErrorHandler.showError(errorMessage);
                    } else {
                        // Fallback error handling
                        alert(errorMessage);
                    }
                }
            })
            .finally(() => {
                if (typeof setLoadingState === 'function') {
                    setLoadingState(false);
                }
            });
        } catch (err) {
            console.error("Error in generateFlashcards:", err);
            
            if (typeof ErrorHandler !== 'undefined' && typeof ErrorHandler.showError === 'function') {
                ErrorHandler.showError('Error generating flashcards: ' + err.message);
            } else {
                // Fallback error handling
                alert('Error generating flashcards: ' + err.message);
            }
            
            if (typeof setLoadingState === 'function') {
                setLoadingState(false);
            }
        }
    };
}

// Initialize everything when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add quiz options UI to the form
    addQuizOptionsUI();
    
    // Enhance the generateFlashcards function
    enhanceGenerateFlashcards();
    
    // Add CSS styles for quiz preview
    const styleElement = document.createElement('style');
    styleElement.id = 'quiz-preview-styles';
    styleElement.textContent = `
        #quiz-preview-container {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .quiz-preview-content {
            margin: 15px 0;
        }
        
        .question-item {
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            background: #f9fafb;
        }
        
        .question-option {
            transition: all 0.2s ease;
        }
        
        .question-option:hover {
            background-color: #f3f4f6;
        }
        
        .quiz-preview-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
        }
        
        .edit-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            flex: 1;
            min-width: 130px;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }
        
        .edit-btn i {
            font-size: 14px;
        }
        
        .edit-btn {
            background-color: #3b82f6;
        }
        
        .regenerate-btn {
            background-color: #f59e0b;
        }
        
        .save-btn {
            background-color: #10b981;
        }
        
        .edit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    `;
    document.head.appendChild(styleElement);
});

/**
 * Enhanced Flashcard and Quiz Fixes
 * 
 * This script addresses several issues:
 * 1. Fixes the quiz question count to respect user input (default 5 instead of 10)
 * 2. Ensures flashcard content is properly displayed in the preview
 * 3. Maintains proper functioning of the flashcard link
 */

// Main initialization function
function initEnhancedFlashcardFixes() {
    console.log("Initializing enhanced flashcard and quiz fixes...");
    
    // Fix quiz options to respect user input with default of 5
    fixQuizOptions();
    
    // Enhance flashcard content display
    enhanceFlashcardDisplay();
    
    // Ensure link generation still works properly
    ensureFlashcardLinkGeneration();
}
  
// Fix quiz options to respect user input
function fixQuizOptions() {
    // Set default quiz question count to 5 instead of 10
    const questionCountInput = document.getElementById('quiz-question-count');
    if (questionCountInput) {
        questionCountInput.value = 5;
        console.log("Set default quiz question count to 5");
    }
    
    // Override the getQuizOptions function to ensure it gets the right values
    window.getQuizOptions = function() {
        const options = {};
        
        try {
            const questionCount = document.getElementById('quiz-question-count');
            if (questionCount) {
                options.questionCount = parseInt(questionCount.value) || 5; // Default to 5 if invalid
            } else {
                options.questionCount = 5; // Default if element not found
            }
            
            const timeLimit = document.getElementById('quiz-time-limit');
            if (timeLimit) {
                options.timeLimit = parseInt(timeLimit.value) || 30;
            }
            
            const questionType = document.querySelector('input[name="quiz-question-type"]:checked');
            if (questionType) {
                options.questionType = questionType.value;
            }
            
            const quizMode = document.querySelector('input[name="quiz-mode"]:checked');
            if (quizMode) {
                options.quizMode = quizMode.value;
            }
        } catch (e) {
            console.error("Error getting quiz options:", e);
            // Return default options in case of error
            return {
                questionCount: 5,
                timeLimit: 30,
                questionType: 'multiple_choice',
                quizMode: 'list'
            };
        }
        
        console.log("Quiz options:", options);
        return options;
    };
    
    // Override QuizManager's generateQuiz function to enforce user question count
    if (typeof window.QuizManager !== 'undefined' && window.QuizManager.generateQuiz) {
        const originalGenerateQuiz = window.QuizManager.generateQuiz;
        
        window.QuizManager.generateQuiz = function(setId) {
            if (!setId) {
                if (typeof ErrorHandler !== 'undefined') {
                    ErrorHandler.showError("No flashcard set available. Please generate flashcards first.");
                } else {
                    alert("No flashcard set available. Please generate flashcards first.");
                }
                return;
            }
            
            // Make sure the UI is created
            if (!document.getElementById('quiz-preview-container')) {
                this.createQuizUI();
            }
            
            const container = document.getElementById('quiz-questions-container');
            if (container) {
                container.innerHTML = `
                <div class="loading" style="text-align: center; padding: 20px;">
                    Generating quiz preview...
                </div>
                `;
            }
            
            // Show the preview container
            const previewContainer = document.getElementById('quiz-preview-container');
            if (previewContainer) {
                previewContainer.style.display = 'block';
            }
            
            // Get quiz options with emphasis on user's question count
            const quizOptions = window.getQuizOptions();
            const questionCount = quizOptions.questionCount || 5; // Ensure we have a default
            
            // Get flashcard data
            fetch(`/api/flashcard-set/${setId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Failed to load flashcard set (${response.status})`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (!data.flashcards || data.flashcards.length === 0) {
                        throw new Error("No flashcards found to create quiz questions");
                    }
                    
                    // Generate quiz data, strictly enforcing user's question count
                    const requestData = {
                        topic: data.flashcard_set.title || "Flashcard Quiz",
                        grade_level: data.flashcard_set.grade_level || "all",
                        numQuestions: questionCount, // Use the user's setting or our default of 5
                        types: [quizOptions.questionType || "multiple_choice"],
                        mode: quizOptions.quizMode || "list",
                        time_limit: quizOptions.timeLimit || 30,
                        content_text: data.flashcards.map(card => `${card.front}: ${card.back}`).join("\n\n")
                    };
                    
                    console.log("Sending quiz generation request with options:", requestData);
                    
                    return fetch('/api/generate-quiz', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${getAuthToken()}`
                        },
                        body: JSON.stringify(requestData)
                    });
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Failed to generate quiz (${response.status})`);
                    }
                    return response.json();
                })
                .then(quizData => {
                    if (!quizData || (!quizData.quiz_data && !quizData.quiz_id)) {
                        throw new Error("Invalid quiz data received from server");
                    }
                    
                    // Get quiz data from response
                    const quiz = quizData.quiz_data || {};
                    quiz.flashcard_set_id = setId;
                    
                    // Ensure we have the right number of questions
                    if (quiz.questions && quiz.questions.length > questionCount) {
                        console.log(`Limiting quiz to ${questionCount} questions as requested (was ${quiz.questions.length})`);
                        quiz.questions = quiz.questions.slice(0, questionCount);
                    }
                    
                    // Store in localStorage for persistence
                    try {
                        localStorage.setItem(`flashcard_quiz_${setId}`, JSON.stringify(quiz));
                    } catch (e) {
                        console.warn("Failed to store quiz data in localStorage:", e);
                    }
                    
                    // Display the preview
                    this.displayQuiz(quiz);
                    
                    // Also try to save to server
                    if (this.saveQuizToServer) {
                        this.saveQuizToServer(setId, quiz)
                        .catch(error => {
                            console.warn("Failed to save quiz to server, but it's saved locally:", error);
                        });
                    }
                })
                .catch(error => {
                    console.error("Error generating quiz:", error);
                    
                    // Show error in container
                    const container = document.getElementById('quiz-questions-container');
                    if (container) {
                        container.innerHTML = `
                        <div class="error-message" style="padding: 15px; background: #fee2e2; color: #b91c1c; border-radius: 8px;">
                            <h3>Error Generating Quiz</h3>
                            <p>${error.message}</p>
                            <button id="retry-quiz-btn" style="margin-top: 10px; padding: 8px 16px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            Try Again
                            </button>
                        </div>
                        `;
                        
                        // Add event listener to retry button
                        document.getElementById('retry-quiz-btn').addEventListener('click', () => this.generateQuiz(setId));
                    }
                });
        };
    }
}

// Helper function to get auth token
function getAuthToken() {
    // Try multiple storage locations for better mobile compatibility
    if (typeof TokenManager !== 'undefined' && typeof TokenManager.getToken === 'function') {
        return TokenManager.getToken();
    }
    
    return localStorage.getItem('token') || 
           sessionStorage.getItem('token') || 
           getCookie('token');
}

// Helper function to get cookie
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// Enhance flashcard display to show actual content
function enhanceFlashcardDisplay() {
    // Override the updateActiveCard function to ensure content is displayed
    window.updateActiveCard = function() {
        if (!window.flashcards || window.flashcards.length === 0) {
            console.warn("No flashcards available to display");
            return;
        }
        
        // Make sure currentCardIndex is within bounds
        if (typeof window.currentCardIndex === 'undefined' || window.currentCardIndex < 0) {
            window.currentCardIndex = 0;
        }
        if (window.currentCardIndex >= window.flashcards.length) {
            window.currentCardIndex = window.flashcards.length - 1;
        }
        
        // Get the current card
        const card = window.flashcards[window.currentCardIndex];
        
        // Update the front and back content
        const frontContent = document.getElementById('card-front-content');
        const backContent = document.getElementById('card-back-content');
        
        if (frontContent) frontContent.textContent = card.front || "Front content unavailable";
        if (backContent) backContent.textContent = card.back || "Back content unavailable";
        
        // Reset flip state
        const flashcardElem = document.getElementById('active-flashcard');
        if (flashcardElem) flashcardElem.classList.remove('flipped');
        
        // Update indicators
        const indicators = document.querySelectorAll('.card-dot');
        indicators.forEach((dot, i) => {
            dot.classList.toggle('active', i === window.currentCardIndex);
        });
        
        console.log(`Updated active card to index ${window.currentCardIndex}:`, card);
    };
    
    // Enhanced handleFlashcardSuccess to properly handle content
    window.handleFlashcardSuccess = function(data) {
        try {
            console.log("Handling flashcard success with data:", data);
            
            // Store flashcard set ID
            window.flashcardSetId = data.flashcard_set_id;
            
            // Store flashcards - ensure proper data mapping
            window.flashcards = Array.isArray(data.flashcards) ? data.flashcards.map(card => ({
                id: card.id || `card-${Math.random().toString(36).substring(2, 9)}`,
                front: card.front || "Front side",
                back: card.back || "Back side",
                type: card.type || "definition"
            })) : [];
            
            window.currentCardIndex = 0;
            
            // Display flashcards
            const flashcardPreview = document.getElementById('flashcard-preview');
            if (flashcardPreview) {
                flashcardPreview.style.display = 'block';
                
                // Render card indicators
                renderCardIndicators();
                
                // Update the active card display
                updateActiveCard();
                
                // Apply appearance settings if available
                if (typeof applyColorSettings === 'function') {
                    applyColorSettings();
                }
                
                // Scroll to the flashcard preview
                setTimeout(() => {
                    flashcardPreview.scrollIntoView({ behavior: 'smooth' });
                }, 300);
            }
            
            // Display the flashcard link
            displayFlashcardLink(data.flashcard_set_id, data.quiz_id);
            
            // Check if auto-generate quiz is enabled
            const autoGenerateQuiz = document.getElementById('auto-generate-quiz')?.checked ?? true;
            if (autoGenerateQuiz && typeof window.QuizManager !== 'undefined') {
                setTimeout(() => {
                    if (!document.getElementById('quiz-preview-container')) {
                        window.QuizManager.createQuizUI();
                    }
                    window.QuizManager.generateQuiz(data.flashcard_set_id);
                }, 1000);
            }
        } catch (err) {
            console.error("Error handling flashcard success:", err);
            alert('Error displaying flashcards. Please try again.');
        }
    };
}

// Ensure the flashcard link generation still works
function ensureFlashcardLinkGeneration() {
    // Function to display flashcard link
    window.displayFlashcardLink = function(flashcardSetId, quizId) {
        console.log("Displaying flashcard link for set ID:", flashcardSetId);
        
        // Get the link container element
        const linkContainer = document.getElementById('flashcard-link');
        if (!linkContainer) {
            console.error("flashcard-link element not found");
            return;
        }
        
        // Generate the base URL
        const baseUrl = window.location.origin || 'https://seashell-app-onfk3.ondigitalocean.app';
        let flashcardUrl = `${baseUrl}/flashcards.html?id=${flashcardSetId}`;
        
        // Add quiz ID if available
        if (quizId) {
            flashcardUrl += `&quiz=${quizId}`;
        }
        
        // Add appearance parameters if available
        if (typeof window.flashcardColors !== 'undefined') {
            const colors = window.flashcardColors;
            const appearanceParams = new URLSearchParams();
            appearanceParams.set('fb', encodeURIComponent(colors.frontBackground || '#ffffff'));
            appearanceParams.set('ft', encodeURIComponent(colors.frontText || '#333333'));
            appearanceParams.set('bb', encodeURIComponent(colors.backBackground || '#f0f9ff'));
            appearanceParams.set('bt', encodeURIComponent(colors.backText || '#333333'));
            appearanceParams.set('cb', encodeURIComponent(colors.cardBorder || '#e0e0e0'));
            appearanceParams.set('snow', colors.showSnowflakes ? '1' : '0');
            
            // Add to URL
            flashcardUrl += '&' + appearanceParams.toString();
        }
        
        // Create the HTML content for the link section
        const linkHtml = `
            <div class="success-message">
                <h3>Flashcards${quizId ? ' and Quiz' : ''} Generated Successfully!</h3>
                <p>Share this link with your students:</p>
                <div class="flashcard-url">
                    <input type="text" value="${flashcardUrl}" readonly onclick="this.select()">
                    <button class="copy-button" onclick="copyFlashcardLink('${flashcardUrl}')">
                        Copy
                    </button>
                </div>
                <div class="link-details">
                    <p><strong>✓ Flashcards:</strong> Students can study the flashcards</p>
                    ${quizId ? '<p><strong>✓ Quiz:</strong> A "Take Quiz" button will appear after study</p>' : ''}
                </div>
                <div class="action-buttons">
                    <a href="${flashcardUrl}" target="_blank" class="preview-link-btn">
                        Preview Flashcards
                    </a>
                    ${!quizId ? `
                        <button id="quiz-conversion-btn" class="btn">
                            Create Quiz from Flashcards
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Update the link container and display it
        linkContainer.innerHTML = linkHtml;
        linkContainer.style.display = 'block';
        
        // Add event listener to the quiz conversion button if present
        if (!quizId) {
            setTimeout(() => {
                const quizBtn = document.getElementById('quiz-conversion-btn');
                if (quizBtn) {
                    quizBtn.addEventListener('click', function() {
                        if (typeof QuizManager !== 'undefined' && typeof QuizManager.generateQuiz === 'function') {
                            QuizManager.generateQuiz(flashcardSetId);
                        } else {
                            // Fallback to simple quiz conversion
                            window.location.href = `/quiz-creator?convert_from=flashcards&flashcard_set_id=${flashcardSetId}`;
                        }
                    });
                }
            }, 100);
        }
        
        // Scroll to the link section
        setTimeout(() => {
            linkContainer.scrollIntoView({ behavior: 'smooth' });
        }, 500);
    };
    
    // Copy flashcard link to clipboard
    window.copyFlashcardLink = function(url) {
        // Check if navigator.clipboard is available
        if (navigator.clipboard) {
            navigator.clipboard.writeText(url)
                .then(() => {
                    const copyButton = document.querySelector('.copy-button');
                    if (copyButton) {
                        copyButton.textContent = 'Copied!';
                        copyButton.style.backgroundColor = '#10B981';
                        setTimeout(() => {
                            copyButton.textContent = 'Copy';
                            copyButton.style.backgroundColor = '';
                        }, 2000);
                    }
                })
                .catch(err => {
                    console.error('Failed to copy:', err);
                    fallbackCopyText(url);
                });
        } else {
            fallbackCopyText(url);
        }
    };
    
    // Fallback copy method for browsers without clipboard API
    function fallbackCopyText(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            const copyButton = document.querySelector('.copy-button');
            if (copyButton) {
                copyButton.textContent = successful ? 'Copied!' : 'Copy';
                copyButton.style.backgroundColor = successful ? '#10B981' : '';
                
                if (successful) {
                    setTimeout(() => {
                        copyButton.textContent = 'Copy';
                        copyButton.style.backgroundColor = '';
                    }, 2000);
                }
            }
        } catch (err) {
            console.error('Fallback copy failed:', err);
            alert('Could not copy text. Please select and copy manually.');
        }
        
        document.body.removeChild(textArea);
    }
}

// Helper function for TokenManager if not defined
if (typeof TokenManager === 'undefined') {
    window.TokenManager = {
        getToken: function() {
            return localStorage.getItem('token') || 
                   sessionStorage.getItem('token') || 
                   getCookie('token');
        },
        clearToken: function() {
            localStorage.removeItem('token');
            sessionStorage.removeItem('token');
            document.cookie = 'token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        }
    };
}

// Add quiz options UI with default of 5 questions
function addQuizOptionsUI() {
    // Find the flashcard parameters form group
    const parametersSection = document.querySelector('.form-group h2')?.closest('.form-group');
    if (!parametersSection) {
        console.warn("Could not find parameters section to add quiz options");
        return;
    }
    
    // Check if quiz options already exist
    if (document.getElementById('quiz-options-container')) {
        console.log("Quiz options already exist, updating defaults");
        const questionCount = document.getElementById('quiz-question-count');
        if (questionCount) questionCount.value = 5;
        return;
    }
    
    // Create quiz options form group
    const quizOptionsGroup = document.createElement('div');
    quizOptionsGroup.className = 'form-group';
    quizOptionsGroup.innerHTML = `
        <h2>Quiz Options</h2>
        <div style="margin-bottom: 15px;">
            <input type="checkbox" id="auto-generate-quiz" checked>
            <label for="auto-generate-quiz" style="display: inline; margin-left: 8px; font-weight: normal;">
                Automatically generate a quiz from flashcards
            </label>
        </div>
        
        <div id="quiz-options-container" style="padding: 15px; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
            <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 15px;">
                <div style="flex: 1; min-width: 200px;">
                    <label for="quiz-question-count">Number of Questions:</label>
                    <input type="number" id="quiz-question-count" min="3" max="20" value="5" style="width: 100%; padding: 8px; border: 1px solid #e2e8f0; border-radius: 4px;">
                </div>
                
                <div style="flex: 1; min-width: 200px;">
                    <label for="quiz-time-limit">Time Limit (minutes):</label>
                    <input type="number" id="quiz-time-limit" min="5" max="120" value="30" style="width: 100%; padding: 8px; border: 1px solid #e2e8f0; border-radius: 4px;">
                </div>
            </div>
            
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 10px;">Question Type:</label>
                <div style="display: flex; flex-wrap: wrap; gap: 15px;">
                    <div style="display: flex; align-items: center;">
                        <input type="radio" name="quiz-question-type" id="quiz-type-multiple-choice" value="multiple_choice" checked>
                        <label for="quiz-type-multiple-choice" style="margin-left: 8px; font-weight: normal;">Multiple Choice</label>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <input type="radio" name="quiz-question-type" id="quiz-type-true-false" value="true_false">
                        <label for="quiz-type-true-false" style="margin-left: 8px; font-weight: normal;">True/False</label>
                    </div>
                </div>
            </div>
            
            <div>
                <label style="display: block; margin-bottom: 10px;">Quiz Mode:</label>
                <div style="display: flex; flex-wrap: wrap; gap: 15px;">
                    <div style="display: flex; align-items: center;">
                        <input type="radio" name="quiz-mode" id="quiz-mode-list" value="list" checked>
                        <label for="quiz-mode-list" style="margin-left: 8px; font-weight: normal;">List View (All questions at once)</label>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <input type="radio" name="quiz-mode" id="quiz-mode-auto" value="auto">
                        <label for="quiz-mode-auto" style="margin-left: 8px; font-weight: normal;">Auto Mode (One question at a time)</label>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Insert after parameters section
    parametersSection.parentNode.insertBefore(quizOptionsGroup, parametersSection.nextSibling);
    
    // Add event listener to toggle options visibility
    const autoGenerateCheckbox = document.getElementById('auto-generate-quiz');
    const optionsContainer = document.getElementById('quiz-options-container');
    
    if (autoGenerateCheckbox && optionsContainer) {
        autoGenerateCheckbox.addEventListener('change', function() {
            optionsContainer.style.display = this.checked ? 'block' : 'none';
        });
    }
    
    console.log("Added quiz options UI with default of 5 questions");
}

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add quiz options UI with proper defaults
    addQuizOptionsUI();
    
    // Initialize all the fixes
    initEnhancedFlashcardFixes();
});

// Also run if DOM is already loaded
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    addQuizOptionsUI();
    initEnhancedFlashcardFixes();
}

// Show error message
function showError(message) {
    console.error(message);
    
    // Try to find an error element
    let errorElement = document.querySelector('.error-message');
    
    // If not found, create one
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.style.backgroundColor = '#ffebee';
        errorElement.style.color = '#c62828';
        errorElement.style.padding = '10px';
        errorElement.style.borderRadius = '5px';
        errorElement.style.margin = '10px 0';
        errorElement.style.textAlign = 'center';
        
        // Add to body or container
        const container = document.querySelector('.container') || document.body;
        container.appendChild(errorElement);
    }
    
    // Set message
    errorElement.textContent = message;
    
    // Show the error
    errorElement.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
}

// Add analytics buttons to the score display
function addAnalyticsButtons() {
    // Wait for score container to be created
    const waitForScoreContainer = setInterval(() => {
        const scoreContainer = document.getElementById('score-container');
        if (scoreContainer) {
            clearInterval(waitForScoreContainer);
            
            // Get quiz ID
            const urlParams = new URLSearchParams(window.location.search);
            const quizId = urlParams.get('id') || 
                        (window.quizData && window.quizData.id) || 
                        `flashcard-quiz-${urlParams.get('flashcard_set_id') || 'unknown'}`;
            
            // Create analytics buttons
            const analyticsButtons = document.createElement('div');
            analyticsButtons.className = 'analytics-buttons';
            analyticsButtons.style.display = 'flex';
            analyticsButtons.style.justifyContent = 'center';
            analyticsButtons.style.gap = '10px';
            analyticsButtons.style.marginTop = '20px';
            analyticsButtons.innerHTML = `
                <button class="view-scores-btn" style="background-color: #2196F3; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">
                    📊 View All Scores
                </button>
                <button class="view-analytics-btn" style="background-color: #4CAF50; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer;">
                    📈 Performance Analytics
                </button>
            `;
            
            // Add to score container
            scoreContainer.appendChild(analyticsButtons);
            
            // Add event listeners
            analyticsButtons.querySelector('.view-scores-btn').addEventListener('click', function() {
                window.location.href = `/scores.html?id=${quizId}`;
            });
            
            analyticsButtons.querySelector('.view-analytics-btn').addEventListener('click', function() {
                window.location.href = `/performance.html?id=${quizId}`;
            });
        }
    }, 1000);
}

// Enhanced version of the submitQuiz function to ensure scores are saved
function enhanceSubmitQuiz() {
    // If there's no submitQuiz function, we can't enhance it
    if (typeof window.submitQuiz !== 'function') {
        console.warn("submitQuiz function not found, can't enhance it");
        return;
    }
    
    // Store the original function
    const originalSubmitQuiz = window.submitQuiz;
    
    // Replace with enhanced version
    window.submitQuiz = function() {
        // Call the original function
        originalSubmitQuiz();
        
        // Add our enhancement - ensure quiz results are submitted to server
        setTimeout(() => {
            submitQuizResults();
        }, 500);
    };
}

// Submit quiz results to the server to ensure compatibility with quiz-creator
function submitQuizResults() {
    try {
        // Get quiz data
        const quizData = window.quizData;
        if (!quizData) {
            console.warn("Quiz data not available, can't submit results");
            return;
        }
        
        // Get user answers
        const userAnswers = window.userAnswers || {};
        
        // Prepare submission data
        const score = calculateScore(quizData, userAnswers);
        const maxScore = calculateMaxScore(quizData);
        const timeTaken = calculateTimeTaken();
        const studentName = window.studentName || 'Anonymous Student';
        
        // Get quiz ID
        const urlParams = new URLSearchParams(window.location.search);
        const quizId = urlParams.get('id') || 
                    quizData.id || 
                    `flashcard-quiz-${urlParams.get('flashcard_set_id') || generateRandomId()}`;
        
        // Format answers for submission
        const formattedAnswers = formatAnswersForSubmission(quizData, userAnswers);
        
        // Get authentication token if available
        const token = getAuthToken();
        
        // Headers for submission
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Add token if available
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Submit to server
        fetch(`${config.apiEndpoint}/api/submit-quiz`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                quiz_id: quizId,
                student_name: studentName,
                score: score,
                max_score: maxScore,
                time_taken: timeTaken,
                answers: formattedAnswers,
                is_flashcard_quiz: true
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Quiz results submitted successfully:", data);
        })
        .catch(error => {
            console.error("Failed to submit quiz results:", error);
            
            // Try alternate endpoint
            fetch(`${config.apiEndpoint}/api/save-quiz-results`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    quiz_id: quizId,
                    student_name: studentName,
                    score: score,
                    max_score: maxScore,
                    time_taken: timeTaken,
                    answers: formattedAnswers,
                    is_flashcard_quiz: true
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log("Quiz results submitted to alternate endpoint:", data);
            })
            .catch(error => {
                console.error("Failed to submit to alternate endpoint:", error);
            });
        });
        
    } catch (error) {
        console.error("Error submitting quiz results:", error);
    }
}

// Calculate the user's score
function calculateScore(quizData, userAnswers) {
    let score = 0;
    
    // Go through each question and check if the answer is correct
    quizData.questions.forEach((question, index) => {
        if (question.type === 'multiple_choice' || question.type === 'true_false') {
            const selectedAnswer = userAnswers[index];
            
            if (selectedAnswer !== undefined && 
                question.options && 
                question.options[selectedAnswer] && 
                question.options[selectedAnswer].isCorrect) {
                score++;
            }
        }
    });
    
    return score;
}

// Calculate the maximum possible score
function calculateMaxScore(quizData) {
    let maxScore = 0;
    
    // Count how many questions have scorable answers (multiple choice or true/false)
    quizData.questions.forEach(question => {
        if (question.type === 'multiple_choice' || question.type === 'true_false') {
            maxScore++;
        }
    });
    
    return maxScore;
}

// Calculate time taken to complete the quiz
function calculateTimeTaken() {
    // Try to get from window.timeLeft if available
    if (typeof window.timeLeft === 'number' && typeof window.quizData === 'object') {
        const totalTime = window.quizData.time_limit * 60 || 1800; // Default to 30 mins
        return totalTime - window.timeLeft;
    }
    
    // Default to 10 minutes if we can't calculate
    return 600;
}

// Format answers for submission
function formatAnswersForSubmission(quizData, userAnswers) {
    const formattedAnswers = {};
    
    // Go through each question and format the answer
    quizData.questions.forEach((question, index) => {
        const selectedAnswer = userAnswers[index];
        
        // Skip if no answer was provided
        if (selectedAnswer === undefined) return;
        
        // Add to formatted answers
        formattedAnswers[index] = {
            questionId: question.id || `q${index}`,
            selectedOption: selectedAnswer,
            isCorrect: false,
            answerType: question.type
        };
        
        // Check if the answer is correct for multiple choice questions
        if (question.type === 'multiple_choice' || question.type === 'true_false') {
            if (question.options && question.options[selectedAnswer]) {
                formattedAnswers[index].isCorrect = question.options[selectedAnswer].isCorrect;
            }
        }
    });
    
    return formattedAnswers;
}

// Generate a random ID
function generateRandomId() {
    return Math.random().toString(36).substring(2, 15) + 
           Math.random().toString(36).substring(2, 15);
}

// Initialize the enhanced functionality on both pages
function initEnhancements() {
    // Initialize on flashcard page
    if (config.isFlashcardPage()) {
        enhanceFlashcardPage();
    }
    
    // Initialize on quiz page
    if (config.isQuizPage()) {
        enhanceQuizPage();
        
        // Also enhance submit function to ensure consistent score tracking
        enhanceSubmitQuiz();
        
        // Add analytics buttons to the score display
        addAnalyticsButtons();
    }
    
    // Enhance quiz redirect functionality regardless of page
    enhanceQuizRedirect();
    
    console.log("Flashcard quiz enhancements initialized successfully");
}

// Initialize the configuration and fixes
initializeConfig();

// Call the main initialization function
initEnhancements();

// Make sure the config object is properly initialized
function initializeConfig() {
    // Define the global config object if it doesn't exist
    if (typeof window.config === 'undefined') {
        window.config = {
            // API endpoint
            apiEndpoint: window.location.origin || 'https://seashell-app-onfk3.ondigitalocean.app',
            
            // Helper to check if we're on the flashcard page
            isFlashcardPage: function() {
                return window.location.pathname.includes('flashcards.html') || 
                      document.getElementById('flashcard-preview') !== null;
            },
            
            // Helper to check if we're on the quiz page
            isQuizPage: function() {
                return window.location.pathname.includes('quiz.html') || 
                      document.querySelector('.quiz-container') !== null;
            }
        };
    }
    
    // Make sure config is accessible in the global scope
    window.config = config;
}