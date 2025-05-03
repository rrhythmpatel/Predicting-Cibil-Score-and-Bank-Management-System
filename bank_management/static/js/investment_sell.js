document.addEventListener('DOMContentLoaded', function() {
    console.log('Investment sell script loaded');
    addSellButtons();
});

function addSellButtons() {
    console.log('Adding sell buttons');
    const investmentRows = document.querySelectorAll('table tbody tr');
    console.log('Found rows:', investmentRows.length);
    
    investmentRows.forEach((row, index) => {
        // Skip empty rows
        if (row.querySelector('td[colspan]')) {
            return;
        }
        
        // Get the last cell (Status column)
        const cells = row.querySelectorAll('td');
        if (cells.length < 1) return;
        
        const lastCell = cells[cells.length - 1];
        
        // Get investment ID from data attribute
        let investmentId = row.getAttribute('data-investment-id');
        if (!investmentId) {
            // Use index as fallback
            investmentId = index + 1;
            row.setAttribute('data-investment-id', investmentId);
        }
        
        // Get stock name from first cell
        const stockName = cells[0].textContent.trim();
        const currentValue = cells[3] ? cells[3].textContent.trim() : '$0.00';
        
        // Create sell button if it doesn't exist
        if (!lastCell.querySelector('.sell-btn')) {
            const sellBtn = document.createElement('button');
            sellBtn.className = 'btn btn-sm btn-danger ms-2 sell-btn';
            sellBtn.textContent = 'Sell';
            sellBtn.setAttribute('data-investment-id', investmentId);
            
            sellBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Sell button clicked for investment ID:', investmentId);
                showSellModal(investmentId, stockName, currentValue);
            });
            
            lastCell.appendChild(sellBtn);
        }
    });
}

function showSellModal(investmentId, stockName, currentValue) {
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="sellInvestmentModal" tabindex="-1" aria-labelledby="sellInvestmentModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="sellInvestmentModalLabel">Sell Investment: ${stockName}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>Current Value: ${currentValue}</p>
                        <form id="sellInvestmentForm">
                            <input type="hidden" name="investment_id" value="${investmentId}">
                            <div class="mb-3">
                                <label for="sellQuantity" class="form-label">Quantity to Sell</label>
                                <input type="number" class="form-control" id="sellQuantity" name="quantity" min="1" required>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-danger" id="confirmSellBtn">Confirm Sell</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to the page
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);
    
    // Initialize the modal
    const modal = new bootstrap.Modal(document.getElementById('sellInvestmentModal'));
    modal.show();
    
    // Handle confirm button click
    document.getElementById('confirmSellBtn').addEventListener('click', function() {
        const form = document.getElementById('sellInvestmentForm');
        const quantity = form.querySelector('#sellQuantity').value;
        
        if (quantity > 0) {
            // Send sell request to server
            fetch(`/investment/sell/${investmentId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    quantity: quantity
                })
            })
            .then(response => response.json())
            .then(data => {
                modal.hide();
                
                if (data.success) {
                    // Show success message
                    showAlert('success', data.message || 'Investment sold successfully!');
                    // Reload the page after a short delay
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    // Show error message
                    showAlert('danger', data.message || 'Error selling investment.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                modal.hide();
                showAlert('danger', 'Error processing your request. Please try again.');
            });
        }
    });
    
    // Clean up when modal is hidden
    document.getElementById('sellInvestmentModal').addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modalContainer);
    });
}

function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to the page
    const container = document.querySelector('.container-fluid') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}