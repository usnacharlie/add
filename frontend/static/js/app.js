// Main JavaScript for Political Party Membership System

// Initialize on document ready
$(document).ready(function() {
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();

    // Initialize popovers
    $('[data-bs-toggle="popover"]').popover();

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert:not(.alert-permanent)').fadeOut('slow');
    }, 5000);

    // Add loading spinner to forms
    $('form').on('submit', function() {
        const submitBtn = $(this).find('button[type="submit"]');
        submitBtn.prop('disabled', true);
        submitBtn.html('<span class="spinner-border spinner-border-sm me-2"></span>Processing...');
    });

    // Initialize data tables if present
    if ($.fn.DataTable && $('.data-table').length) {
        $('.data-table').DataTable({
            responsive: true,
            pageLength: 25,
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            }
        });
    }

    // Handle dynamic form fields
    initializeDynamicForms();

    // Setup CSRF token for AJAX requests
    setupCSRFToken();

    // Initialize notification system
    initializeNotifications();
});

// Dynamic form field handling
function initializeDynamicForms() {
    // Province -> District -> Constituency -> Ward cascade
    $('#province_id').on('change', function() {
        const provinceId = $(this).val();
        loadDistricts(provinceId);
    });

    $('#district_id').on('change', function() {
        const districtId = $(this).val();
        loadConstituencies(districtId);
    });

    $('#constituency_id').on('change', function() {
        const constituencyId = $(this).val();
        loadWards(constituencyId);
    });
}

// Load districts based on province
function loadDistricts(provinceId) {
    if (!provinceId) {
        $('#district_id').html('<option value="">Select Province First</option>').prop('disabled', true);
        return;
    }

    $.ajax({
        url: `/auth/api/districts/${provinceId}`,
        method: 'GET',
        success: function(data) {
            let options = '<option value="">Select District</option>';
            data.forEach(district => {
                options += `<option value="${district.id}">${district.name}</option>`;
            });
            $('#district_id').html(options).prop('disabled', false);
            $('#constituency_id').html('<option value="">Select District First</option>').prop('disabled', true);
            $('#ward_id').html('<option value="">Select Constituency First</option>').prop('disabled', true);
        },
        error: function() {
            showAlert('Failed to load districts', 'error');
        }
    });
}

// Load constituencies based on district
function loadConstituencies(districtId) {
    if (!districtId) {
        $('#constituency_id').html('<option value="">Select District First</option>').prop('disabled', true);
        return;
    }

    $.ajax({
        url: `/auth/api/constituencies/${districtId}`,
        method: 'GET',
        success: function(data) {
            let options = '<option value="">Select Constituency</option>';
            data.forEach(constituency => {
                options += `<option value="${constituency.id}">${constituency.name}</option>`;
            });
            $('#constituency_id').html(options).prop('disabled', false);
            $('#ward_id').html('<option value="">Select Constituency First</option>').prop('disabled', true);
        },
        error: function() {
            showAlert('Failed to load constituencies', 'error');
        }
    });
}

// Load wards based on constituency
function loadWards(constituencyId) {
    if (!constituencyId) {
        $('#ward_id').html('<option value="">Select Constituency First</option>').prop('disabled', true);
        return;
    }

    $.ajax({
        url: `/auth/api/wards/${constituencyId}`,
        method: 'GET',
        success: function(data) {
            let options = '<option value="">Select Ward</option>';
            data.forEach(ward => {
                options += `<option value="${ward.id}">${ward.name}</option>`;
            });
            $('#ward_id').html(options).prop('disabled', false);
        },
        error: function() {
            showAlert('Failed to load wards', 'error');
        }
    });
}

// Setup CSRF token for AJAX requests
function setupCSRFToken() {
    const token = $('meta[name="csrf-token"]').attr('content');

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", token);
            }
        }
    });
}

// Show alert messages
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    $('#alert-container').html(alertHtml);

    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
}

// Initialize notification system
function initializeNotifications() {
    // Check for new notifications every 30 seconds
    setInterval(checkNotifications, 30000);
}

// Check for new notifications
function checkNotifications() {
    $.ajax({
        url: '/api/notifications/check',
        method: 'GET',
        success: function(data) {
            if (data.count > 0) {
                updateNotificationBadge(data.count);
            }
        }
    });
}

// Update notification badge
function updateNotificationBadge(count) {
    const badge = $('.notification-badge');
    if (count > 0) {
        if (badge.length) {
            badge.text(count);
        } else {
            $('.notifications-icon').append(`<span class="notification-badge">${count}</span>`);
        }
    } else {
        badge.remove();
    }
}

// Handle payment processing
function processPayment(paymentType, amount, method) {
    showLoadingSpinner();

    $.ajax({
        url: '/member/payments/make',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            payment_type: paymentType,
            amount: amount,
            payment_method: method
        }),
        success: function(data) {
            hideLoadingSpinner();
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Payment Initiated',
                    text: `Reference: ${data.reference}`,
                    confirmButtonText: 'OK'
                });
            } else {
                Swal.fire('Error', data.message, 'error');
            }
        },
        error: function() {
            hideLoadingSpinner();
            Swal.fire('Error', 'Failed to process payment', 'error');
        }
    });
}

// Show loading spinner
function showLoadingSpinner() {
    $('body').append(`
        <div class="spinner-overlay">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `);
}

// Hide loading spinner
function hideLoadingSpinner() {
    $('.spinner-overlay').remove();
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-ZM', {
        style: 'currency',
        currency: 'ZMW'
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-ZM', options);
}

// Handle file uploads
function handleFileUpload(inputId, maxSize = 5242880) { // 5MB default
    const fileInput = document.getElementById(inputId);
    const file = fileInput.files[0];

    if (file) {
        if (file.size > maxSize) {
            showAlert(`File size must be less than ${maxSize / 1048576}MB`, 'error');
            fileInput.value = '';
            return false;
        }

        const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
        if (!allowedTypes.includes(file.type)) {
            showAlert('Only JPEG, PNG, and PDF files are allowed', 'error');
            fileInput.value = '';
            return false;
        }

        return true;
    }

    return false;
}

// Print membership card
function printMembershipCard() {
    window.print();
}

// Export data to CSV
function exportToCSV(data, filename) {
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Convert data to CSV format
function convertToCSV(data) {
    if (!data || !data.length) return '';

    const headers = Object.keys(data[0]);
    const csvHeaders = headers.join(',');

    const csvRows = data.map(row => {
        return headers.map(header => {
            const value = row[header] || '';
            return `"${value.toString().replace(/"/g, '""')}"`;
        }).join(',');
    });

    return [csvHeaders, ...csvRows].join('\n');
}

// Validate NRC number format
function validateNRC(nrcNumber) {
    const nrcPattern = /^\d{6}\/\d{2}\/\d$/;
    return nrcPattern.test(nrcNumber);
}

// Validate phone number format
function validatePhone(phoneNumber) {
    const phonePattern = /^0\d{9}$/;
    return phonePattern.test(phoneNumber);
}

// Session timeout warning
let sessionTimeout;
function resetSessionTimeout() {
    clearTimeout(sessionTimeout);
    sessionTimeout = setTimeout(function() {
        Swal.fire({
            title: 'Session Expiring',
            text: 'Your session will expire in 5 minutes. Do you want to continue?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Continue',
            cancelButtonText: 'Logout'
        }).then((result) => {
            if (result.isConfirmed) {
                $.get('/api/session/refresh');
                resetSessionTimeout();
            } else {
                window.location.href = '/auth/logout';
            }
        });
    }, 25 * 60 * 1000); // 25 minutes
}

// Initialize session timeout on page load
if ($('body').data('authenticated')) {
    resetSessionTimeout();
    $(document).on('click keypress', resetSessionTimeout);
}