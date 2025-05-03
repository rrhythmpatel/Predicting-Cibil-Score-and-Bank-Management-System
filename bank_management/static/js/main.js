// Document Ready Function
$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    })

    // Example AJAX function for future use
    function makeAjaxCall(url, method, data) {
        return $.ajax({
            url: url,
            method: method,
            data: data,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
    }

    // Get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';')
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim()
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                    break
                }
            }
        }
        return cookieValue
    }

    // Form submission handler
    $('form').on('submit', function(e) {
        e.preventDefault()
        const form = $(this)
        const url = form.attr('action')
        const method = form.attr('method')
        const data = form.serialize()

        makeAjaxCall(url, method, data)
            .done(function(response) {
                // Handle success
                if (response.message) {
                    showAlert('success', response.message)
                }
            })
            .fail(function(error) {
                // Handle error
                showAlert('danger', 'An error occurred. Please try again.')
            })
    })

    // Show alert function
    function showAlert(type, message) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `
        $('.container').prepend(alertHtml)
        
        // Auto dismiss after 5 seconds
        setTimeout(function() {
            $('.alert').alert('close')
        }, 5000)
    }
})