document.addEventListener('DOMContentLoaded', function() {
    // Fetch market data
    fetchMarketData();
    
    // Set up search functionality
    document.getElementById('stock-search-form')?.addEventListener('submit', function(e) {
        e.preventDefault();
        const symbol = document.getElementById('stock-symbol').value;
        if (symbol) {
            fetchStockData(symbol);
        }
    });
    
    // Fix URL references to create_investment_page
    fixCreateInvestmentPageUrls();
});

// Add this new function to fix URL references
function fixCreateInvestmentPageUrls() {
    // Find all links that point to create_investment_page
    const links = document.querySelectorAll('a[href*="create_investment_page"]');
    links.forEach(link => {
        // Replace with the correct URL
        link.href = '/investment/create/';
        link.setAttribute('data-url-fixed', 'true');
    });
    
    // Also fix any form actions
    const forms = document.querySelectorAll('form[action*="create_investment_page"]');
    forms.forEach(form => {
        form.action = '/investment/create/';
        form.setAttribute('data-url-fixed', 'true');
    });
}

function fetchMarketData() {
    // Fetch market data
    fetch('/api/market_data/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('sp500-value').textContent = data.sp500.value;
            document.getElementById('sp500-change').textContent = data.sp500.change + '%';
            document.getElementById('sp500-change').className = data.sp500.change >= 0 ? 'text-success' : 'text-danger';
            
            document.getElementById('nasdaq-value').textContent = data.nasdaq.value;
            document.getElementById('nasdaq-change').textContent = data.nasdaq.change + '%';
            document.getElementById('nasdaq-change').className = data.nasdaq.change >= 0 ? 'text-success' : 'text-danger';
            
            document.getElementById('nifty-value').textContent = data.nifty.value;
            document.getElementById('nifty-change').textContent = data.nifty.change + '%';
            document.getElementById('nifty-change').className = data.nifty.change >= 0 ? 'text-success' : 'text-danger';
        })
        .catch(error => {
            console.error('Error fetching market data:', error);
            document.getElementById('sp500-value').textContent = 'Error loading data';
            document.getElementById('nasdaq-value').textContent = 'Error loading data';
            document.getElementById('nifty-value').textContent = 'Error loading data';
        });
}

function fetchStockData(symbol) {
    // Add validation for the symbol
    if (!symbol || symbol.trim() === '' || symbol.toLowerCase() === 'unknown') {
        document.getElementById('stock-result').innerHTML = `
            <div class="alert alert-warning mt-3">
                Please enter a valid stock symbol (e.g., AAPL, MSFT, GOOGL).
            </div>
        `;
        return;
    }
    
    fetch(`/api/stock_data/${symbol}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Display stock data
            const resultDiv = document.getElementById('stock-result');
            resultDiv.innerHTML = `
                <div class="card mt-3">
                    <div class="card-header">
                        <h5>${data.name} (${data.symbol})</h5>
                    </div>
                    <div class="card-body">
                        <p class="card-text">Price: $${data.price}</p>
                        <p class="card-text">Change: <span class="${data.change >= 0 ? 'text-success' : 'text-danger'}">${data.change}%</span></p>
                        <p class="card-text">Volume: ${data.volume}</p>
                        <button class="btn btn-primary" onclick="showInvestmentForm('${data.symbol}', '${data.name}', ${data.price})">Invest Now</button>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error('Error fetching stock data:', error);
            document.getElementById('stock-result').innerHTML = `
                <div class="alert alert-danger mt-3">
                    Error fetching data for ${symbol}. Please try again with a valid stock symbol.
                </div>
            `;
        });
}

function showInvestmentForm(symbol, name, price) {
    const formDiv = document.getElementById('investment-form');
    
    // Get CSRF token
    let csrfToken = '';
    const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
    
    if (!csrfElement) {
        console.error('CSRF token not found');
        formDiv.innerHTML = `
            <div class="alert alert-danger mt-3">
                Error: CSRF token not found. Please refresh the page and try again.
            </div>
        `;
        return;
    }
    
    csrfToken = csrfElement.value;
    
    formDiv.innerHTML = `
        <div class="card mt-3">
            <div class="card-header">
                <h5>Invest in ${name} (${symbol})</h5>
            </div>
            <div class="card-body">
                <form id="investment-form-submit">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                    <input type="hidden" name="symbol" value="${symbol}">
                    <input type="hidden" name="stock_name" value="${name}">
                    <input type="hidden" name="price_per_share" value="${price}">
                    <input type="hidden" name="investment_type" value="stock">
                    
                    <div class="form-group">
                        <label for="shares">Number of Shares</label>
                        <input type="number" class="form-control" id="shares" name="shares" min="1" required>
                    </div>
                    
                    <div class="form-group mt-3">
                        <label for="account_id">Account</label>
                        <select class="form-control" id="account_id" name="account_id" required>
                            <option value="">Select an account</option>
                        </select>
                    </div>
                    
                    <div class="form-group mt-3">
                        <label>Total Cost</label>
                        <p id="total-cost" class="form-control-static">$0.00</p>
                    </div>
                    
                    <button type="button" class="btn btn-success mt-3" id="confirm-investment-btn">Confirm Investment</button>
                </form>
            </div>
        </div>
    `;
    
    // Calculate total cost when shares change
    const sharesInput = document.getElementById('shares');
    sharesInput.addEventListener('input', function() {
        const shares = parseInt(this.value) || 0;
        const totalCost = shares * price;
        document.getElementById('total-cost').textContent = '$' + totalCost.toFixed(2);
    });
    
    // Modify the part of showInvestmentForm function that fetches account data:
    
    // Fetch and populate user accounts
    fetch('/api/user_accounts/')
        .then(response => response.json())
        .then(accounts => {
            const accountSelect = document.getElementById('account_id');
            if (!accounts || accounts.length === 0) {
                accountSelect.innerHTML = '<option value="">No accounts available</option>';
                console.error('No accounts found for the user');
                return;
            }
            
            // Clear existing options
            accountSelect.innerHTML = '<option value="">Select an account</option>';
            
            // Just use the accounts data directly without additional API calls
            accounts.forEach(account => {
                const option = document.createElement('option');
                option.value = account.id;
                option.textContent = `${account.account_number} (Balance: $${parseFloat(account.balance).toFixed(2)})`;
                accountSelect.appendChild(option);
            });
            
            // Add event listener to update total cost when account changes
            accountSelect.addEventListener('change', function() {
                // Update UI to show available balance for selected account
                const selectedOption = this.options[this.selectedIndex];
                if (selectedOption && selectedOption.value) {
                    const sharesInput = document.getElementById('shares');
                    const shares = parseInt(sharesInput.value) || 0;
                    const totalCost = shares * price;
                    document.getElementById('total-cost').textContent = '$' + totalCost.toFixed(2);
                    
                    // You could also add validation here to check if the account has enough balance
                }
            });
        })
        .catch(error => {
            console.error('Error fetching accounts:', error);
            const accountSelect = document.getElementById('account_id');
            accountSelect.innerHTML = '<option value="">Error loading accounts</option>';
        });
    
    // Handle button click
    document.getElementById('confirm-investment-btn').addEventListener('click', function() {
        const form = document.getElementById('investment-form-submit');
        const formData = new FormData(form);
        
        // Show loading state
        this.textContent = 'Processing...';
        this.disabled = true;
        
        fetch('/investment/create/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Server error');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                formDiv.innerHTML = `
                    <div class="alert alert-success">
                        ${data.message || 'Investment successful!'}
                        <div class="mt-3">
                            <a href="/investments/" class="btn btn-primary">View My Investments</a>
                        </div>
                    </div>
                `;
                
                // Add a script to fix any template issues with create_investment_page
                const fixScript = document.createElement('script');
                fixScript.innerHTML = `
                    // Fix for missing create_investment_page URL
                    document.addEventListener('DOMContentLoaded', function() {
                        const links = document.querySelectorAll('a[href*="create_investment_page"]');
                        links.forEach(link => {
                            link.href = '/investment/create/';
                            link.setAttribute('data-url-fixed', 'true');
                        });
                    });
                `;
                document.head.appendChild(fixScript);
            } else {
                throw new Error(data.message || 'Error creating investment');
            }
        })
        .catch(error => {
            document.getElementById('confirm-investment-btn').textContent = 'Confirm Investment';
            document.getElementById('confirm-investment-btn').disabled = false;
            
            formDiv.innerHTML += `
                <div class="alert alert-danger mt-3">
                    ${error.message || 'Error processing your investment. Please try again.'}
                </div>
            `;
        });
    });

// Investment page functionality
$(document).ready(function() {
    // Directly fetch accounts from the API
    $.ajax({
        url: '/api/user-accounts/',
        type: 'GET',
        success: function(response) {
            console.log("Account data received:", response);
            
            if (response.success && response.accounts && response.accounts.length > 0) {
                // Update account dropdown
                const accountSelect = $('#account');
                accountSelect.empty();
                accountSelect.append('<option value="">Select an account</option>');
                
                response.accounts.forEach(account => {
                    accountSelect.append(`
                        <option value="${account.id}" data-balance="${account.balance}">
                            ${account.account_number} (Balance: $${account.balance.toFixed(2)})
                        </option>
                    `);
                });
            } else {
                $('#account').html('<option value="">No accounts available</option>');
                console.error("No accounts found in response:", response);
            }
        },
        error: function(xhr, status, error) {
            console.error("Error loading accounts:", error);
            $('#account').html('<option value="">Error loading accounts</option>');
        }
    });
    
    // Calculate total cost when number of shares changes
    $(document).on('input', '#shares', function() {
        const shares = $(this).val() || 0;
        const price = parseFloat($('#stock-price').text().replace('$', '')) || 0;
        const totalCost = shares * price;
        $('#total-cost').text('$' + totalCost.toFixed(2));
    });
    
    // Handle stock search form submission
    $('#stock-search-form').submit(function(e) {
        e.preventDefault();
        const symbol = $('#stock-symbol').val().trim();
        
        if (!symbol) {
            alert('Please enter a stock symbol');
            return;
        }
        
        // Mock stock data (in a real app, you would fetch this from an API)
        const stockData = {
            symbol: symbol.toUpperCase(),
            name: getStockName(symbol.toUpperCase()),
            price: getRandomPrice(),
            change: getRandomChange(),
            volume: getRandomVolume()
        };
        
        // Display stock information
        $('#stock-result').html(`
            <div class="card mt-3">
                <div class="card-header bg-primary text-white">
                    <h4>${stockData.name} (${stockData.symbol})</h4>
                </div>
                <div class="card-body">
                    <p><strong>Price:</strong> <span id="stock-price">$${stockData.price.toFixed(2)}</span></p>
                    <p><strong>Change:</strong> ${stockData.change.toFixed(2)}%</p>
                    <p><strong>Volume:</strong> ${stockData.volume.toLocaleString()}</p>
                    <button class="btn btn-success" id="invest-now-btn">Invest Now</button>
                </div>
            </div>
        `);
    });
    
    // Handle Invest Now button click
    $(document).on('click', '#invest-now-btn', function() {
        const symbol = $('#stock-result h4').text().match(/\(([^)]+)\)/)[1];
        const name = $('#stock-result h4').text().replace(` (${symbol})`, '');
        const price = parseFloat($('#stock-price').text().replace('$', ''));
        
        $('#investment-form').html(`
            <div class="card mt-3">
                <div class="card-header bg-primary text-white">
                    <h4>Invest in ${name} (${symbol})</h4>
                </div>
                <div class="card-body">
                    <form id="confirm-investment-form">
                        <input type="hidden" name="symbol" value="${symbol}">
                        <input type="hidden" name="stock_name" value="${name}">
                        <input type="hidden" name="price_per_share" value="${price}">
                        
                        <div class="form-group">
                            <label for="shares">Number of Shares</label>
                            <input type="number" class="form-control" id="shares" name="shares" min="1" step="1" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="account">Account</label>
                            <select class="form-control" id="investment-account" name="account_id" required>
                                <!-- Options will be copied from the main account dropdown -->
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Total Cost: <span id="total-cost">$0.00</span></label>
                        </div>
                        
                        <button type="submit" class="btn btn-primary">Confirm Investment</button>
                    </form>
                </div>
            </div>
        `);
        
        // Copy account options to the investment form
        $('#account option').each(function() {
            $('#investment-account').append($(this).clone());
        });
    });
    
    // Handle investment form submission
    $(document).on('submit', '#confirm-investment-form', function(e) {
        e.preventDefault();
        
        const shares = $('#shares').val();
        const accountId = $('#investment-account').val();
        
        if (!shares || shares <= 0) {
            alert('Please enter a valid number of shares');
            return;
        }
        
        if (!accountId) {
            alert('Please select an account');
            return;
        }
        
        // In a real app, you would submit this to your backend
        alert('Investment submitted successfully!');
        
        // Refresh the page to show updated portfolio
        window.location.reload();
    });
    
    // Helper functions for mock data
    function getStockName(symbol) {
        const stockNames = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'META': 'Meta Platforms Inc.',
            'TSLA': 'Tesla Inc.',
            'NVDA': 'NVIDIA Corporation',
            'RELIANCE.NS': 'Reliance Industries Ltd.'
        };
        
        return stockNames[symbol] || `${symbol} Corp`;
    }
    
    function getRandomPrice() {
        return Math.random() * 900 + 100;
    }
    
    function getRandomChange() {
        return (Math.random() * 10) - 5;
    }
    
    function getRandomVolume() {
        return Math.floor(Math.random() * 20000000) + 1000000;
    }
});
