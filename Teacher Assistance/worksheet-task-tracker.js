/**
 * Worksheet Task Tracker
 * Sends worksheet completion/score data to the quiz management dashboard.
 * This script is loaded by student-worksheet.html after the main worksheet logic.
 */
(function() {
    'use strict';

    // Listen for worksheet submission results
    // The main script dispatches a custom event after results are shown
    function trackWorksheetCompletion(resultData) {
        if (!resultData) return;

        try {
            // Store the latest submission in sessionStorage for cross-page reference
            const submissionRecord = {
                worksheet_id: new URLSearchParams(window.location.search).get('id'),
                total_score: resultData.totalScore || 0,
                total_possible: resultData.totalPossible || 0,
                percentage: resultData.totalPossible > 0
                    ? Math.round((resultData.totalScore / resultData.totalPossible) * 100)
                    : 0,
                evaluated_by_ai: resultData.evaluatedByAI || false,
                timestamp: new Date().toISOString()
            };

            // Save to sessionStorage for dashboard to pick up
            const existing = JSON.parse(sessionStorage.getItem('worksheetSubmissions') || '[]');
            existing.push(submissionRecord);
            sessionStorage.setItem('worksheetSubmissions', JSON.stringify(existing));

            // Also save to localStorage for persistent cross-session tracking
            const persistentRecords = JSON.parse(localStorage.getItem('worksheetSubmissions') || '[]');
            persistentRecords.push(submissionRecord);
            // Keep only last 50 submissions in localStorage
            if (persistentRecords.length > 50) {
                persistentRecords.splice(0, persistentRecords.length - 50);
            }
            localStorage.setItem('worksheetSubmissions', JSON.stringify(persistentRecords));

        } catch (e) {
            console.log('Worksheet tracker: could not save submission record', e);
        }
    }

    // Hook into the showResults function by observing the feedback section
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.target.classList && mutation.target.classList.contains('show')) {
                // Feedback section became visible - extract score from badge
                var scoreBadge = document.getElementById('scoreBadge');
                if (scoreBadge) {
                    var parts = scoreBadge.textContent.split('/');
                    if (parts.length === 2) {
                        trackWorksheetCompletion({
                            totalScore: parseInt(parts[0]) || 0,
                            totalPossible: parseInt(parts[1]) || 0,
                            evaluatedByAI: document.getElementById('aiBadge') &&
                                           document.getElementById('aiBadge').style.display !== 'none'
                        });
                    }
                }
            }
        });
    });

    // Start observing the feedback section once DOM is ready
    function initTracker() {
        var feedbackSection = document.getElementById('feedbackSection');
        if (feedbackSection) {
            observer.observe(feedbackSection, {
                attributes: true,
                attributeFilter: ['class']
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // Small delay to ensure the main script has rendered
            setTimeout(initTracker, 500);
        });
    } else {
        setTimeout(initTracker, 500);
    }
})();
