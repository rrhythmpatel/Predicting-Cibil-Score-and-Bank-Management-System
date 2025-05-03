// CIBIL Score Visualization
document.addEventListener('DOMContentLoaded', function() {
    // Check if the CIBIL score element exists on the page
    const cibilScoreElement = document.getElementById('cibil-score-value');
    if (!cibilScoreElement) return;
    
    // Get the CIBIL score value
    const cibilScore = parseInt(cibilScoreElement.textContent || '0');
    
    // Initialize the gauge chart if the element exists
    const gaugeElement = document.getElementById('cibil-gauge');
    if (gaugeElement) {
        renderCibilGauge(gaugeElement, cibilScore);
    }
});

// Function to render the CIBIL score gauge
function renderCibilGauge(element, score) {
    // Calculate percentage (CIBIL scores range from 300 to 900)
    const percentage = ((score - 300) / 600) * 100;
    
    // Determine color based on score
    let color = '#dc3545'; // Red for poor
    if (score >= 750) {
        color = '#28a745'; // Green for excellent
    } else if (score >= 700) {
        color = '#17a2b8'; // Blue for good
    } else if (score >= 650) {
        color = '#ffc107'; // Yellow for fair
    }
    
    // Create gauge chart using Chart.js
    new Chart(element, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [percentage, 100 - percentage],
                backgroundColor: [color, '#e9ecef'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '80%',
            circumference: 180,
            rotation: 270,
            plugins: {
                tooltip: {
                    enabled: false
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true
            }
        }
    });
}