// ============================================
// QUIZ HISTORY AND MANAGEMENT COMPONENT
// ============================================

// Main entry point for quiz management page
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the quiz management page
    if (document.getElementById('quiz-management-dashboard')) {
      const quizManager = new QuizHistoryManager();
      quizManager.init();
    }
    
    // Check if we're on a quiz page and process mode if specified
    if (document.getElementById('quiz-content')) {
      initializeQuizMode();
    }
  });
  
  /**
   * Initialize appropriate quiz mode based on URL parameters
   */
  function initializeQuizMode() {
    const urlParams = new URLSearchParams(window.location.search);
    const quizId = urlParams.get('id');
    const mode = urlParams.get('mode') || 'relaxed';
    
    if (!quizId) return;
    
    // Get mode-specific options
    const modeOptions = {};
    
    if (mode === 'collaboration') {
      modeOptions.numTeams = parseInt(urlParams.get('teams') || '2');
      modeOptions.teamNaming = urlParams.get('teamNaming') || 'letters';
      
      // Parse team names if provided
      const teamNamesParam = urlParams.get('teamNames');
      if (teamNamesParam) {
        modeOptions.teamNames = teamNamesParam.split(',').map(name => decodeURIComponent(name));
      }
    }
    
    // Create appropriate mode handler
    const modeHandler = QuizModeFactory.createModeHandler(mode, quizId, modeOptions);
    
    // Initialize the mode
    modeHandler.init();
  }
  
  /**
   * Quiz History Management System
   * - Displays historical quizzes without requiring a quiz ID
   * - Supports different quiz modes (Relaxed, Competition, Collaboration)
   */
  class QuizHistoryManager {
    constructor() {
      this.quizData = [];
      this.filteredQuizData = [];
      this.currentPage = 1;
      this.rowsPerPage = 10;
      this.sortField = 'created_at';
      this.sortDirection = 'desc';
      this.filters = {
        searchTerm: '',
        dateRange: 'all',
        quizType: 'all'
      };
    }
  
    /**
     * Initialize the quiz history dashboard
     */
    async init() {
      try {
        this.showLoading(true);
        
        // Attach event listeners
        this.attachEventListeners();
        
        // Load quiz history data
        await this.loadQuizHistory();
        
        // Render the quiz history table
        this.renderQuizHistoryTable();
        
        this.showLoading(false);
      } catch (error) {
        console.error('Error initializing quiz history:', error);
        this.showError('Failed to load quiz history. Please try again.');
        this.showLoading(false);
      }
    }
    
    /**
     * Attach event listeners for filtering, sorting, and pagination
     */
    attachEventListeners() {
      // Search input
      document.getElementById('searchInput')?.addEventListener('input', () => {
        this.filters.searchTerm = document.getElementById('searchInput').value.toLowerCase();
        this.currentPage = 1;
        this.applyFilters();
      });
      
      // Date range filter
      document.getElementById('dateFilter')?.addEventListener('change', () => {
        this.filters.dateRange = document.getElementById('dateFilter').value;
        this.currentPage = 1;
        this.applyFilters();
      });
      
      // Quiz type filter
      document.getElementById('quizTypeFilter')?.addEventListener('change', () => {
        this.filters.quizType = document.getElementById('quizTypeFilter').value;
        this.currentPage = 1;
        this.applyFilters();
      });
      
      // Create quiz button
      document.getElementById('createQuizBtn')?.addEventListener('click', () => {
        window.location.href = '/quiz-creator';
      });
    }
    
    /**
     * Load quiz history data from API
     */
    async loadQuizHistory() {
      try {
        const token = this.getAuthToken();

        let quizzes = [];

        // Load quizzes from quiz API (requires auth)
        if (token) {
          try {
            const response = await fetch('https://seashell-app-onfk3.ondigitalocean.app/user/quizzes', {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });

            if (response.ok) {
              const data = await response.json();
              quizzes = (data.quizzes || []).map(q => ({ ...q, source: 'quiz' }));
            }
          } catch (quizErr) {
            console.warn('Could not load quizzes:', quizErr);
          }
        }

        // Also load worksheets (public, no auth required)
        try {
          const wsResponse = await fetch('/api/worksheet-submissions');
          if (wsResponse.ok) {
            const wsData = await wsResponse.json();
            const worksheets = (wsData.worksheets || []).map(ws => ({
              id: ws.id,
              title: ws.title,
              topic: ws.subject || '',
              grade_level: '-',
              time_limit: null,
              mode: 'worksheet',
              quiz_mode: 'worksheet',
              created_at: ws.created_at,
              submission_count: ws.submission_count || 0,
              average_score: ws.average_score || 0,
              source: 'worksheet'
            }));
            quizzes = quizzes.concat(worksheets);
          }
        } catch (wsErr) {
          console.warn('Could not load worksheets:', wsErr);
        }

        this.quizData = quizzes;
        this.filteredQuizData = [...this.quizData];

        // Sort by creation date (newest first)
        this.sortQuizzes('created_at', 'desc');

      } catch (error) {
        console.error('Error loading quiz history:', error);
        throw error;
      }
    }
    
    /**
     * Apply filters to quiz data
     */
    applyFilters() {
      this.filteredQuizData = this.quizData.filter(quiz => {
        // Search term filter
        const matchesSearch = quiz.title.toLowerCase().includes(this.filters.searchTerm) || 
                             quiz.topic.toLowerCase().includes(this.filters.searchTerm);
        
        // Date range filter
        let matchesDate = true;
        const quizDate = new Date(quiz.created_at);
        const today = new Date();
        
        if (this.filters.dateRange === 'today') {
          matchesDate = quizDate.toDateString() === today.toDateString();
        } else if (this.filters.dateRange === 'week') {
          const weekStart = new Date(today);
          weekStart.setDate(today.getDate() - today.getDay());
          matchesDate = quizDate >= weekStart;
        } else if (this.filters.dateRange === 'month') {
          matchesDate = quizDate.getMonth() === today.getMonth() && 
                       quizDate.getFullYear() === today.getFullYear();
        }
        
        // Quiz type filter
        let matchesType = true;
        if (this.filters.quizType !== 'all') {
          matchesType = (quiz.quiz_mode || 'relaxed') === this.filters.quizType;
        }
        
        return matchesSearch && matchesDate && matchesType;
      });
      
      // Re-sort the filtered data
      this.sortQuizzes(this.sortField, this.sortDirection);
      
      // Render the table with new filters
      this.renderQuizHistoryTable();
    }
    
    /**
     * Sort quizzes by the specified field and direction
     */
    sortQuizzes(field, direction) {
      this.sortField = field;
      this.sortDirection = direction;
      
      this.filteredQuizData.sort((a, b) => {
        let valueA = a[field];
        let valueB = b[field];
        
        // Handle dates
        if (field === 'created_at') {
          valueA = new Date(valueA);
          valueB = new Date(valueB);
        }
        
        // Compare values
        if (valueA < valueB) {
          return direction === 'asc' ? -1 : 1;
        }
        if (valueA > valueB) {
          return direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    
    /**
     * Render the quiz history table
     */
    renderQuizHistoryTable() {
      const tableBody = document.getElementById('quizHistoryBody');
      const noResults = document.getElementById('noResults');
      
      if (!tableBody) return;
      
      // Clear the table
      tableBody.innerHTML = '';
      
      if (this.filteredQuizData.length === 0) {
        // Show no results message
        if (noResults) noResults.style.display = 'block';
        return;
      }
      
      // Hide no results message
      if (noResults) noResults.style.display = 'none';
      
      // Calculate pagination
      const startIndex = (this.currentPage - 1) * this.rowsPerPage;
      const endIndex = Math.min(startIndex + this.rowsPerPage, this.filteredQuizData.length);
      const paginatedQuizzes = this.filteredQuizData.slice(startIndex, endIndex);
      
      // Render table rows
      paginatedQuizzes.forEach(quiz => {
        const row = document.createElement('tr');
        
        // Format date
        const createdDate = new Date(quiz.created_at);
        const formattedDate = createdDate.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        });
        
        // Determine quiz mode display text and badge class
        let modeText = 'Relaxed';
        let modeClass = 'mode-relaxed';

        if (quiz.quiz_mode === 'worksheet') {
          modeText = 'Worksheet';
          modeClass = 'mode-worksheet';
        } else if (quiz.quiz_mode === 'competition') {
          modeText = 'Competition';
          modeClass = 'mode-competition';
        } else if (quiz.quiz_mode === 'collaboration') {
          modeText = 'Collaboration';
          modeClass = 'mode-collaboration';
        }
        
        row.innerHTML = `
          <td class="quiz-title-cell">
            <div class="quiz-info">
              <div class="quiz-title">${quiz.title}</div>
              <div class="quiz-topic">${quiz.topic}</div>
            </div>
          </td>
          <td><span class="quiz-grade">${quiz.grade_level}</span></td>
          <td><span class="mode-badge ${modeClass}">${modeText}</span></td>
          <td>${formattedDate}</td>
          <td>
            <div class="quiz-actions">
              <button class="action-btn view-scores-btn" data-id="${quiz.id}" title="View Scores">
                📊
              </button>
              <button class="action-btn view-analytics-btn" data-id="${quiz.id}" title="View Analytics">
                📈
              </button>
              <button class="action-btn share-btn" data-id="${quiz.id}" title="Share Quiz">
                🔗
              </button>
            </div>
          </td>
        `;
        
        // Add event listeners for action buttons
        const viewScoresBtn = row.querySelector('.view-scores-btn');
        if (viewScoresBtn) {
          viewScoresBtn.addEventListener('click', () => {
            if (quiz.source === 'worksheet') {
              window.location.href = `/scores.html?worksheet_id=${quiz.id}`;
            } else {
              window.location.href = `/scores.html?id=${quiz.id}`;
            }
          });
        }

        const viewAnalyticsBtn = row.querySelector('.view-analytics-btn');
        if (viewAnalyticsBtn) {
          viewAnalyticsBtn.addEventListener('click', () => {
            if (quiz.source === 'worksheet') {
              window.location.href = `/performance.html?worksheet_id=${quiz.id}`;
            } else {
              window.location.href = `/performance.html?id=${quiz.id}`;
            }
          });
        }
        
        const shareBtn = row.querySelector('.share-btn');
        if (shareBtn) {
          shareBtn.addEventListener('click', () => {
            this.showShareQuizModal(quiz);
          });
        }
        
        tableBody.appendChild(row);
      });
      
      // Update pagination
      this.setupPagination();
    }
    
    /**
     * Set up pagination controls
     */
    setupPagination() {
      const paginationElement = document.getElementById('pagination');
      if (!paginationElement) return;
      
      paginationElement.innerHTML = '';
      
      const totalPages = Math.ceil(this.filteredQuizData.length / this.rowsPerPage);
      
      if (totalPages <= 1) {
        return;
      }
      
      // Previous button
      const prevButton = document.createElement('button');
      prevButton.className = `page-btn ${this.currentPage === 1 ? 'disabled' : ''}`;
      prevButton.innerHTML = '&laquo;';
      if (this.currentPage > 1) {
        prevButton.addEventListener('click', () => {
          this.currentPage--;
          this.renderQuizHistoryTable();
        });
      }
      paginationElement.appendChild(prevButton);
      
      // Page numbers
      const maxPagesToShow = 5;
      let startPage = Math.max(1, this.currentPage - Math.floor(maxPagesToShow / 2));
      let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);
      
      if (endPage - startPage + 1 < maxPagesToShow) {
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
      }
      
      for (let i = startPage; i <= endPage; i++) {
        const pageButton = document.createElement('button');
        pageButton.className = `page-btn ${i === this.currentPage ? 'active' : ''}`;
        pageButton.textContent = i;
        pageButton.addEventListener('click', () => {
          this.currentPage = i;
          this.renderQuizHistoryTable();
        });
        paginationElement.appendChild(pageButton);
      }
      
      // Next button
      const nextButton = document.createElement('button');
      nextButton.className = `page-btn ${this.currentPage === totalPages ? 'disabled' : ''}`;
      nextButton.innerHTML = '&raquo;';
      if (this.currentPage < totalPages) {
        nextButton.addEventListener('click', () => {
          this.currentPage++;
          this.renderQuizHistoryTable();
        });
      }
      paginationElement.appendChild(nextButton);
    }
    
    /**
     * Show quiz sharing modal
     */
    showShareQuizModal(quiz) {
      // Create modal container
      const modal = document.createElement('div');
      modal.className = 'modal';
      modal.id = 'shareQuizModal';
      modal.style.display = 'flex';
      
      // Create basic quiz URL
      const quizUrl = `https://seashell-app-onfk3.ondigitalocean.app/quiz.html?id=${quiz.id}`;
      
      // Create modal content
      modal.innerHTML = `
        <div class="modal-content">
          <span class="close">&times;</span>
          <h2>Share Quiz: ${quiz.title}</h2>
          
          <div class="share-options">
            <div class="share-option-group">
              <h3>Basic Quiz Link</h3>
              <div class="quiz-url-container">
                <input type="text" value="${quizUrl}" readonly class="quiz-url" id="basicQuizUrl">
                <button class="copy-btn" data-target="basicQuizUrl">Copy</button>
              </div>
            </div>
            
            <div class="share-option-group">
              <h3>Quiz Mode</h3>
              <div class="quiz-mode-selector">
                <div class="mode-option">
                  <input type="radio" id="modeRelaxed" name="quizMode" value="relaxed" checked>
                  <label for="modeRelaxed">Relaxed (Normal)</label>
                  <p class="mode-description">Standard quiz format for individual assessment.</p>
                </div>
                
                <div class="mode-option">
                  <input type="radio" id="modeCompetition" name="quizMode" value="competition">
                  <label for="modeCompetition">Competition</label>
                  <p class="mode-description">Competitive mode with a winners board.</p>
                </div>
                
                <div class="mode-option">
                  <input type="radio" id="modeCollaboration" name="quizMode" value="collaboration">
                  <label for="modeCollaboration">Collaboration</label>
                  <p class="mode-description">Team-based format where answers are combined.</p>
                </div>
              </div>
            </div>
            
            <div id="teamSettings" class="share-option-group" style="display: none;">
              <h3>Team Settings</h3>
              <div class="team-settings-controls">
                <div class="setting-group">
                  <label for="numTeams">Number of Teams:</label>
                  <select id="numTeams">
                    <option value="2">2 Teams</option>
                    <option value="3">3 Teams</option>
                    <option value="4">4 Teams</option>
                    <option value="5">5 Teams</option>
                  </select>
                </div>
                
                <div class="setting-group">
                  <label for="teamNaming">Team Naming:</label>
                  <select id="teamNaming">
                    <option value="letters">Letters (Team A, Team B, etc.)</option>
                    <option value="numbers">Numbers (Team 1, Team 2, etc.)</option>
                    <option value="colors">Colors (Red Team, Blue Team, etc.)</option>
                    <option value="custom">Custom Names</option>
                  </select>
                </div>
              </div>
              
              <div id="customTeamNames" style="display: none;">
                <h4>Custom Team Names</h4>
                <div id="teamNameInputs">
                  <div class="team-name-input">
                    <label for="team1">Team 1:</label>
                    <input type="text" id="team1" placeholder="Enter team name">
                  </div>
                  <div class="team-name-input">
                    <label for="team2">Team 2:</label>
                    <input type="text" id="team2" placeholder="Enter team name">
                  </div>
                </div>
              </div>
            </div>
            
            <div class="share-option-group">
              <h3>Academy Settings (Optional)</h3>
              <div class="setting-group">
                <label for="academyName">Academy Name:</label>
                <input type="text" id="academyName" placeholder="Enter academy name (optional)">
              </div>
            </div>
          </div>
          
          <div class="generated-link">
            <h3>Generated Quiz Link</h3>
            <div class="quiz-url-container">
              <input type="text" id="generatedQuizUrl" readonly value="${quizUrl}">
              <button class="copy-btn" data-target="generatedQuizUrl">Copy</button>
            </div>
            <p class="share-hint">Share this link with your students to start the quiz.</p>
          </div>
        </div>
      `;
      
      // Add modal to document
      document.body.appendChild(modal);
      
      // Add event listeners
      
      // Close button
      const closeBtn = modal.querySelector('.close');
      closeBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
      });
      
      // Copy buttons
      const copyButtons = modal.querySelectorAll('.copy-btn');
      copyButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          const targetId = btn.getAttribute('data-target');
          const inputElement = document.getElementById(targetId);
          
          if (inputElement) {
            inputElement.select();
            document.execCommand('copy');
            
            // Show copied state
            const originalText = btn.textContent;
            btn.textContent = 'Copied!';
            setTimeout(() => {
              btn.textContent = originalText;
            }, 2000);
          }
        });
      });
      
      // Quiz mode selection
      const modeInputs = modal.querySelectorAll('input[name="quizMode"]');
      const teamSettings = modal.getElementById('teamSettings');
      
      modeInputs.forEach(input => {
        input.addEventListener('change', () => {
          // Show team settings if collaboration mode is selected
          if (input.value === 'collaboration') {
            teamSettings.style.display = 'block';
          } else {
            teamSettings.style.display = 'none';
          }
          
          // Update generated URL
          updateGeneratedUrl();
        });
      });
      
      // Team naming select
      const teamNamingSelect = modal.getElementById('teamNaming');
      const customTeamNames = modal.getElementById('customTeamNames');
      const teamNameInputs = modal.getElementById('teamNameInputs');
      
      teamNamingSelect.addEventListener('change', () => {
        if (teamNamingSelect.value === 'custom') {
          customTeamNames.style.display = 'block';
        } else {
          customTeamNames.style.display = 'none';
        }
        
        // Update generated URL
        updateGeneratedUrl();
      });
      
      // Number of teams select
      const numTeamsSelect = modal.getElementById('numTeams');
      
      numTeamsSelect.addEventListener('change', () => {
        // Update custom team name inputs
        if (teamNamingSelect.value === 'custom') {
          const numTeams = parseInt(numTeamsSelect.value);
          
          // Clear existing inputs
          teamNameInputs.innerHTML = '';
          
          // Create inputs for each team
          for (let i = 1; i <= numTeams; i++) {
            const div = document.createElement('div');
            div.className = 'team-name-input';
            div.innerHTML = `
              <label for="team${i}">Team ${i}:</label>
              <input type="text" id="team${i}" placeholder="Enter team name">
            `;
            teamNameInputs.appendChild(div);
            
            // Add input event listener
            div.querySelector('input').addEventListener('input', updateGeneratedUrl);
          }
        }
        
        // Update generated URL
        updateGeneratedUrl();
      });
      
      // Academy name input
      const academyNameInput = modal.getElementById('academyName');
      academyNameInput.addEventListener('input', updateGeneratedUrl);
      
      // Function to update the generated URL
      function updateGeneratedUrl() {
        const generatedUrlInput = document.getElementById('generatedQuizUrl');
        let url = `https://seashell-app-onfk3.ondigitalocean.app/quiz.html?id=${quiz.id}`;
        
        // Add selected mode
        const selectedMode = document.querySelector('input[name="quizMode"]:checked').value;
        url += `&mode=${selectedMode}`;
        
        // Add team settings if collaboration mode
        if (selectedMode === 'collaboration') {
          // Add number of teams
          const numTeams = numTeamsSelect.value;
          url += `&teams=${numTeams}`;
          
          // Add team naming convention
          const teamNaming = teamNamingSelect.value;
          url += `&teamNaming=${teamNaming}`;
          
          // Add custom team names if selected
          if (teamNaming === 'custom') {
            let teamNames = [];
            for (let i = 1; i <= parseInt(numTeams); i++) {
              const teamNameInput = document.getElementById(`team${i}`);
              if (teamNameInput && teamNameInput.value.trim()) {
                teamNames.push(encodeURIComponent(teamNameInput.value.trim()));
              } else {
                teamNames.push(encodeURIComponent(`Team ${i}`));
              }
            }
            
            url += `&teamNames=${teamNames.join(',')}`;
          }
        }
        
        // Add academy name if provided
        if (academyNameInput.value.trim()) {
          url += `&academy=${encodeURIComponent(academyNameInput.value.trim())}`;
        }
        
        generatedUrlInput.value = url;
      }
      
      // Initialize generated URL
      updateGeneratedUrl();
    }
    
    /**
     * Show loading state
     */
    showLoading(isLoading) {
      const loadingElement = document.getElementById('loading');
      if (loadingElement) {
        loadingElement.style.display = isLoading ? 'block' : 'none';
      }
    }
    
    /**
     * Show error message
     */
    showError(message) {
      const errorElement = document.getElementById('errorMessage');
      if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
          errorElement.style.display = 'none';
        }, 5000);
      }
    }
    
    /**
     * Get authentication token
     */
    getAuthToken() {
      return localStorage.getItem('token') || 
             sessionStorage.getItem('token') || 
             this.getCookie('token');
    }
    
    /**
     * Get cookie value by name
     */
    getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
      return null;
    }
  }
  
  /**
   * Collaboration Mode Handler
   * - Manages team-based quiz taking where answers are combined
   * - Teams can be automatically or manually assigned
   */
  class CollaborationModeHandler {
    constructor(quizId, options = {}) {
      this.quizId = quizId;
      this.options = options;
      this.teams = [];
      this.teamResponses = {};
      
      // Set default options
      this.options.numTeams = this.options.numTeams || 2;
      this.options.teamNaming = this.options.teamNaming || 'letters';
      this.options.teamNames = this.options.teamNames || [];
      
      // Generate team names if not provided
      if (this.options.teamNames.length < this.options.numTeams) {
        this.options.teamNames = this.generateTeamNames(
          this.options.numTeams, 
          this.options.teamNaming
        );
      }
    }
    
    /**
     * Initialize collaboration mode
     */
    async init() {
      try {
        // Create team selection UI
        this.createTeamSelectionUI();
        
        // Load any existing team data
        await this.loadTeamData();
        
        // Add event listeners for team selection
        this.setupTeamSelectionListeners();
        
      } catch (error) {
        console.error('Error initializing collaboration mode:', error);
      }
    }
    
    /**
     * Generate team names based on naming convention
     */
    generateTeamNames(numTeams, namingConvention) {
      const teamNames = [];
      
      switch (namingConvention) {
        case 'letters':
          for (let i = 0; i < numTeams; i++) {
            teamNames.push(`Team ${String.fromCharCode(65 + i)}`); // A, B, C, etc.
          }
          break;
        case 'numbers':
          for (let i = 1; i <= numTeams; i++) {
            teamNames.push(`Team ${i}`);
          }
          break;
        case 'colors':
          const colors = ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange'];
          for (let i = 0; i < numTeams; i++) {
            teamNames.push(`${colors[i % colors.length]} Team`);
          }
          break;
        default:
          // Default to numbered teams
          for (let i = 1; i <= numTeams; i++) {
            teamNames.push(`Team ${i}`);
          }
      }
      
      return teamNames;
    }
    
    /**
     * Create team selection UI before the quiz starts
     */
    createTeamSelectionUI() {
      // Check if team selection UI already exists
      if (document.getElementById('team-selection')) {
        return;
      }
      
      // Find appropriate container for team selection
      const container = document.querySelector('.container') || document.body;
      
      // Create team selection element
      const teamSelectionElement = document.createElement('div');
      teamSelectionElement.id = 'team-selection';
      teamSelectionElement.className = 'team-selection-panel';
      
      // Create HTML content for team selection
      teamSelectionElement.innerHTML = `
        <div class="team-selection-header">
          <h2>Team Collaboration Mode</h2>
          <p>Select your team before starting the quiz</p>
        </div>
        
        <div class="teams-container" id="teams-container">
          ${this.renderTeamOptions()}
        </div>
        
        <div class="team-selection-footer">
          <p class="collaboration-info">
            <strong>How Collaboration Works:</strong> In this mode, your team's score combines the best answers from all team members. If any team member answers a question correctly, the team gets credit for that question.
          </p>
          <div class="team-selection-actions">
            <button id="select-team-btn" class="btn" disabled>Continue with Selected Team</button>
          </div>
        </div>
      `;
      
      // Create styles for team selection
      const styleElement = document.createElement('style');
      styleElement.textContent = `
        .team-selection-panel {
          background: linear-gradient(135deg, #3a7bd5, #00d2ff);
          border-radius: 12px;
          padding: 25px;
          margin-bottom: 30px;
          box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
          color: white;
        }
        
        .team-selection-header {
          text-align: center;
          margin-bottom: 20px;
        }
        
        .team-selection-header h2 {
          font-size: 24px;
          margin-bottom: 5px;
        }
        
        .teams-container {
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          gap: 20px;
          margin: 30px 0;
        }
        
        .team-option {
          width: 150px;
          height: 150px;
          background: rgba(255, 255, 255, 0.1);
          border: 2px solid transparent;
          border-radius: 12px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
          position: relative;
          overflow: hidden;
        }
        
        .team-option:hover {
          background: rgba(255, 255, 255, 0.2);
          transform: translateY(-5px);
        }
        
        .team-option.selected {
          border-color: white;
          background: rgba(255, 255, 255, 0.25);
          transform: translateY(-5px);
          box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
        }
        
        .team-option .team-color {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          margin-bottom: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 28px;
          font-weight: bold;
          color: white;
        }
        
        .team-option .team-name {
          font-weight: 600;
          font-size: 18px;
          text-align: center;
        }
        
        .team-option .team-members {
          font-size: 14px;
          margin-top: 5px;
          opacity: 0.8;
        }
        
        .team-option .members-badge {
          position: absolute;
          top: 10px;
          right: 10px;
          background: rgba(0, 0, 0, 0.3);
          border-radius: 20px;
          padding: 3px 8px;
          font-size: 12px;
        }
        
        .collaboration-info {
          background: rgba(0, 0, 0, 0.1);
          padding: 15px;
          border-radius: 8px;
          margin-bottom: 20px;
          font-size: 14px;
          line-height: 1.5;
        }
        
        .team-selection-actions {
          display: flex;
          justify-content: center;
        }
        
        #select-team-btn {
          padding: 12px 25px;
          background: rgba(255, 255, 255, 0.25);
          color: white;
          border: 2px solid white;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        
        #select-team-btn:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.4);
          transform: translateY(-2px);
        }
        
        #select-team-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `;
      
      // Add team selection UI to DOM
      document.head.appendChild(styleElement);
      
      // Find student name modal and insert after that (if it exists)
      const studentNameModal = document.getElementById('studentNameModal');
      if (studentNameModal) {
        studentNameModal.after(teamSelectionElement);
      } else {
        // Otherwise insert at beginning of container
        container.insertBefore(teamSelectionElement, container.firstChild);
      }
    }
    
    /**
     * Render team options HTML
     */
    renderTeamOptions() {
      const teamColors = [
        '#FF5722', // Red/Orange
        '#2196F3', // Blue
        '#4CAF50', // Green
        '#9C27B0', // Purple
        '#FFC107', // Yellow
        '#00BCD4', // Cyan
        '#795548', // Brown
        '#607D8B'  // Blue-grey
      ];
      
      let html = '';
      
      for (let i = 0; i < this.options.numTeams; i++) {
        const teamName = this.options.teamNames[i] || `Team ${i + 1}`;
        const teamLetter = teamName.charAt(teamName.lastIndexOf(' ') + 1);
        const teamColor = teamColors[i % teamColors.length];
        const memberCount = this.getTeamMemberCount(teamName);
        
        html += `
          <div class="team-option" data-team="${teamName}">
            <div class="team-color" style="background-color: ${teamColor}">
              ${teamLetter}
            </div>
            <div class="team-name">${teamName}</div>
            <div class="members-badge">${memberCount} member${memberCount !== 1 ? 's' : ''}</div>
          </div>
        `;
      }
      
      return html;
    }
    
    /**
     * Get current member count for a team
     */
    getTeamMemberCount(teamName) {
      const team = this.teams.find(t => t.name === teamName);
      return team ? team.members.length : 0;
    }
    
    /**
     * Load existing team data from local storage or server
     */
    async loadTeamData() {
      try {
        // First check local storage for team data
        const storedTeamData = localStorage.getItem(`quiz_${this.quizId}_teams`);
        
        if (storedTeamData) {
          this.teams = JSON.parse(storedTeamData);
        } else {
          // Initialize team data
          this.teams = this.options.teamNames.map(name => ({
            name: name,
            members: []
          }));
        }
        
        // Also try to load from server if available
        const token = this.getAuthToken();
        if (token) {
          try {
            const response = await fetch(`https://seashell-app-onfk3.ondigitalocean.app/api/quiz/${this.quizId}/teams`, {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });
            
            if (response.ok) {
              const serverTeamData = await response.json();
              if (serverTeamData.teams && serverTeamData.teams.length > 0) {
                this.teams = serverTeamData.teams;
              }
            }
          } catch (error) {
            console.warn('Could not load team data from server:', error);
            // Continue with local data
          }
        }
        
        // Update UI with team data
        this.updateTeamMemberCounts();
        
      } catch (error) {
        console.error('Error loading team data:', error);
        // Initialize empty teams as fallback
        this.teams = this.options.teamNames.map(name => ({
          name: name,
          members: []
        }));
      }
    }
    
    /**
     * Update team member counts in UI
     */
    updateTeamMemberCounts() {
      const teamOptions = document.querySelectorAll('.team-option');
      
      teamOptions.forEach(option => {
        const teamName = option.getAttribute('data-team');
        const memberCount = this.getTeamMemberCount(teamName);
        
        const membersBadge = option.querySelector('.members-badge');
        if (membersBadge) {
          membersBadge.textContent = `${memberCount} member${memberCount !== 1 ? 's' : ''}`;
        }
      });
    }
    
    /**
     * Set up event listeners for team selection
     */
    setupTeamSelectionListeners() {
      // Team option selection
      const teamOptions = document.querySelectorAll('.team-option');
      const selectTeamBtn = document.getElementById('select-team-btn');
      
      let selectedTeam = null;
      
      teamOptions.forEach(option => {
        option.addEventListener('click', () => {
          // Remove selected class from all options
          teamOptions.forEach(opt => opt.classList.remove('selected'));
          
          // Add selected class to clicked option
          option.classList.add('selected');
          
          // Store selected team
          selectedTeam = option.getAttribute('data-team');
          
          // Enable continue button
          if (selectTeamBtn) {
            selectTeamBtn.disabled = false;
          }
        });
      });
      
      // Team selection button
      if (selectTeamBtn) {
        selectTeamBtn.addEventListener('click', () => {
          if (selectedTeam) {
            this.handleTeamSelection(selectedTeam);
          }
        });
      }
    }
    
    /**
     * Handle team selection and continue to quiz
     */
    handleTeamSelection(teamName) {
      try {
        // Get student name (if available)
        const studentName = window.studentName || 'Anonymous';
        
        // Find selected team
        const team = this.teams.find(t => t.name === teamName);
        
        if (team) {
          // Add student to team if not already a member
          if (!team.members.includes(studentName)) {
            team.members.push(studentName);
          }
          
          // Save team data to local storage
          localStorage.setItem(`quiz_${this.quizId}_teams`, JSON.stringify(this.teams));
          localStorage.setItem(`quiz_${this.quizId}_selected_team`, teamName);
          
          // Save student's team selection
          this.studentTeam = teamName;
          window.quizTeam = teamName;
          
          // Try to save to server if available
          this.saveTeamDataToServer();
          
          // Hide team selection panel and show quiz
          this.hideTeamSelectionPanel();
        }
      } catch (error) {
        console.error('Error handling team selection:', error);
        // Fall back to hiding the panel anyway
        this.hideTeamSelectionPanel();
      }
    }
    
    /**
     * Save team data to server
     */
    async saveTeamDataToServer() {
      try {
        const token = this.getAuthToken();
        if (!token) return;
        
        await fetch(`https://seashell-app-onfk3.ondigitalocean.app/api/quiz/${this.quizId}/teams`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            teams: this.teams,
            studentTeam: this.studentTeam,
            studentName: window.studentName || 'Anonymous'
          })
        });
      } catch (error) {
        console.warn('Could not save team data to server:', error);
        // Continue without server storage
      }
    }
    
    /**
     * Hide team selection panel and show quiz
     */
    hideTeamSelectionPanel() {
      const teamSelectionPanel = document.getElementById('team-selection');
      if (teamSelectionPanel) {
        teamSelectionPanel.style.display = 'none';
      }
      
      // Show quiz content
      const quizContent = document.getElementById('quiz-content');
      if (quizContent) {
        quizContent.style.display = 'block';
      }
      
      // Create team info banner
      this.createTeamInfoBanner();
      
      // Override quiz submission to include team data
      this.overrideQuizSubmission();
    }
    
    /**
     * Create team info banner to show during quiz
     */
    createTeamInfoBanner() {
      // Check if banner already exists
      if (document.getElementById('team-info-banner')) {
        return;
      }
      
      const container = document.querySelector('.container') || document.body;
      const quizContent = document.getElementById('quiz-content');
      
      // Create banner element
      const bannerElement = document.createElement('div');
      bannerElement.id = 'team-info-banner';
      bannerElement.className = 'team-info-banner';
      
      // Find team color from selection screen
      let teamColor = '#3a7bd5'; // Default color
      const teamOptions = document.querySelectorAll('.team-option');
      teamOptions.forEach(option => {
        if (option.getAttribute('data-team') === this.studentTeam) {
          const colorDiv = option.querySelector('.team-color');
          if (colorDiv) {
            teamColor = window.getComputedStyle(colorDiv).backgroundColor;
          }
        }
      });
      
      bannerElement.innerHTML = `
        <div class="team-banner-content">
          <div class="team-badge" style="background-color: ${teamColor}">
            ${this.studentTeam.charAt(this.studentTeam.lastIndexOf(' ') + 1)}
          </div>
          <div class="team-info">
            <div class="team-name">${this.studentTeam}</div>
            <div class="team-mode">Collaboration Mode</div>
          </div>
        </div>
      `;
      
      // Add styles for banner
      const styleElement = document.createElement('style');
      styleElement.textContent = `
        .team-info-banner {
          background: linear-gradient(to right, rgba(255,255,255,0.9), rgba(255,255,255,0.7));
          border-radius: 8px;
          padding: 10px 15px;
          margin-bottom: 20px;
          display: flex;
          align-items: center;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .team-banner-content {
          display: flex;
          align-items: center;
          gap: 15px;
        }
        
        .team-badge {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
          font-weight: bold;
          color: white;
        }
        
        .team-info .team-name {
          font-weight: 600;
          font-size: 16px;
          color: #333;
        }
        
        .team-info .team-mode {
          font-size: 14px;
          color: #666;
        }
      `;
      
      document.head.appendChild(styleElement);
      
      // Insert banner before quiz content
      if (quizContent) {
        quizContent.parentNode.insertBefore(bannerElement, quizContent);
      } else {
        container.insertBefore(bannerElement, container.firstChild);
      }
    }
    
    /**
     * Override quiz submission function to include team data
     */
    overrideQuizSubmission() {
      // Store original submitQuiz function if it exists
      if (window.submitQuiz && !window.originalSubmitQuiz) {
        window.originalSubmitQuiz = window.submitQuiz;
        
        // Override with team-aware version
        window.submitQuiz = () => {
          try {
            // Run original function to calculate score and show results
            window.originalSubmitQuiz();
            
            // Now add team data to the submission
            this.enhanceSubmissionWithTeamData();
          } catch (error) {
            console.error('Error in team-enhanced submission:', error);
            // Fall back to original submission if available
            if (window.originalSubmitQuiz) {
              window.originalSubmitQuiz();
            }
          }
        };
      }
    }
    
    /**
     * Enhance quiz submission with team data
     */
    enhanceSubmissionWithTeamData() {
      // First, ensure we have team data to work with
      if (!this.studentTeam) {
        console.warn('No team data available for submission enhancement');
        return;
      }
      
      try {
        // Get submission ID from UI or recent submission
        // This would need to be adjusted based on how the quiz stores submission IDs
        const submissionId = this.getLatestSubmissionId();
        
        if (!submissionId) {
          console.warn('Could not find submission ID for team enhancement');
          return;
        }
        
        // Send team data to server
        fetch(`https://seashell-app-onfk3.ondigitalocean.app/api/quiz-submission/${submissionId}/team`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            team: this.studentTeam,
            quiz_id: this.quizId,
            student_name: window.studentName || 'Anonymous'
          })
        })
        .then(response => {
          if (!response.ok) {
            throw new Error(`Failed to add team data: ${response.status}`);
          }
          console.log('Successfully added team data to submission');
        })
        .catch(error => {
          console.error('Error adding team data to submission:', error);
        });
        
      } catch (error) {
        console.error('Error enhancing submission with team data:', error);
      }
    }
    
    /**
     * Get the latest submission ID
     * This is a placeholder that would need to be implemented based on the actual quiz
     */
    getLatestSubmissionId() {
      // In a real implementation, this would get the submission ID from:
      // 1. The response from the submit-quiz API call
      // 2. A DOM element that might contain the submission ID
      // 3. Local storage where it might be saved after submission
      
      // Placeholder implementation to search for an ID in the UI:
      const scoreContainer = document.getElementById('score-container');
      if (scoreContainer && scoreContainer.dataset && scoreContainer.dataset.submissionId) {
        return scoreContainer.dataset.submissionId;
      }
      
      // Fallback: try to find a URL parameter or any element containing submission ID
      const urlParams = new URLSearchParams(window.location.search);
      return urlParams.get('submission_id');
    }
    
    /**
     * Get authentication token
     */
    getAuthToken() {
      return localStorage.getItem('token') || 
             sessionStorage.getItem('token') || 
             this.getCookie('token');
    }
    
    /**
     * Get cookie value by name
     */
    getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
      return null;
    }
  }
          
  
  // ============================================
  // QUIZ MODE HANDLERS
  // ============================================
  
  /**
   * Quiz Mode Factory - Creates the appropriate mode handler
   */
  class QuizModeFactory {
    static createModeHandler(mode, quizId, options = {}) {
      switch (mode) {
        case 'competition':
          return new CompetitionModeHandler(quizId);
        case 'collaboration':
          return new CollaborationModeHandler(quizId, options);
        default:
          return new RelaxedModeHandler(quizId);
      }
    }
  }
  
  /**
   * Basic Relaxed Mode Handler
   * - Standard quiz mode with no special features
   */
  class RelaxedModeHandler {
    constructor(quizId) {
      this.quizId = quizId;
    }
    
    async init() {
      // No special initialization for relaxed mode
      console.log('Relaxed mode initialized for quiz:', this.quizId);
    }
  }
  
  /**
   * Competition Mode Handler
   * - Manages the competition aspects of quizzes
   * - Displays leaderboard and winners
   */
  const styleElement = document.createElement('style');
  styleElement.textContent = `
    .competition-leaderboard {
      background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 30px;
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
      color: white;
    }
    
    .competition-leaderboard h2 {
      text-align: center;
      margin-bottom: 20px;
      font-size: 24px;
    }
    
    .podium {
      display: flex;
      justify-content: center;
      align-items: flex-end;
      height: 180px;
      margin-bottom: 30px;
    }
    
    .podium-place {
      display: flex;
      flex-direction: column;
      align-items: center;
      transition: all 0.3s ease;
    }
    
    .first-place {
      z-index: 3;
    }
    
    .first-place .avatar {
      width: 70px;
      height: 70px;
      background: linear-gradient(45deg, #FFD700, #FFC107);
      border: 3px solid white;
      font-size: 32px;
    }
    
    .first-place .name {
      font-size: 18px;
      font-weight: 700;
    }
    
    .first-place .score {
      font-size: 20px;
    }
    
    .second-place {
      margin-top: 40px;
      z-index: 2;
    }
    
    .second-place .avatar {
      width: 60px;
      height: 60px;
      background: linear-gradient(45deg, #E0E0E0, #BDBDBD);
      border: 2px solid white;
      font-size: 28px;
    }
    
    .third-place {
      margin-top: 70px;
      z-index: 1;
    }
    
    .third-place .avatar {
      width: 50px;
      height: 50px;
      background: linear-gradient(45deg, #CD7F32, #A1662F);
      border: 2px solid white;
      font-size: 24px;
    }
    
    .podium-place .avatar {
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      color: white;
      font-weight: bold;
      margin-bottom: 10px;
    }
    
    .podium-place .name {
      text-align: center;
      font-weight: 600;
      margin-bottom: 5px;
      max-width: 100px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .podium-place .score {
      font-weight: bold;
    }
    
    .leaderboard-table-container {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 10px;
      padding: 15px;
      backdrop-filter: blur(5px);
    }
    
    .leaderboard-table {
      width: 100%;
      border-collapse: collapse;
      color: white;
    }
    
    .leaderboard-table th {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .leaderboard-table td {
      padding: 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .leaderboard-table tr:last-child td {
      border-bottom: none;
    }
    
    .leaderboard-table tr:hover td {
      background: rgba(255, 255, 255, 0.1);
    }
    
    .loading-data {
      text-align: center;
      padding: 20px;
      color: rgba(255, 255, 255, 0.7);
    }
  `;