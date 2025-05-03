document.addEventListener('DOMContentLoaded', function() {
    console.log('Investments.js loaded');
    
    // Set up the sell modal functionality
    const sellModal = document.getElementById('sellModal');
    if (sellModal) {
        console.log('Sell modal found');
        
        // When the modal is shown, set the investment ID
        sellModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const investmentId = button.getAttribute('data-investment-id');
            const stockName = button.getAttribute('data-stock-name');
            
            console.log(`Modal opened with investment ID: ${investmentId}, Stock: ${stockName}`);
            
            // Store the investment ID directly on the modal element
            sellModal.setAttribute('data-current-investment-id', investmentId);
            
            // Update the modal with the investment details
            const modalInvestmentIdField = document.getElementById('modalInvestmentId');
            if (modalInvestmentIdField) {
                modalInvestmentIdField.value = investmentId;
                console.log(`Set modalInvestmentId value to: ${investmentId}`);
            } else {
                console.error('modalInvestmentId field not found');
            }
            
            document.getElementById('sellModalLabel').textContent = `Sell ${stockName}`;
        });
        
        // Handle the form submission
        const sellForm = document.getElementById('sellForm');
        if (sellForm) {
            // Override the form action to use the correct URL
            sellForm.action = '/api/sell_investment/';
            
            sellForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Get the investment ID from the hidden field
                const investmentIdField = document.getElementById('modalInvestmentId');
                const investmentId = investmentIdField ? investmentIdField.value : '';
                
                console.log(`Form submitted with investment ID: ${investmentId}`);
                
                if (!investmentId) {
                    alert('Error: Investment ID is missing');
                    return;
                }
                
                // Use standard form submission
                this.submit();
            });
        }
    }
});