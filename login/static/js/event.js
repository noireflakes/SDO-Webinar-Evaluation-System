

setTimeout(function () {
  document.querySelectorAll('.alert').forEach(function(el) {
    el.style.display = 'none';
  });
}, 10000); 

// Event Comparison Functionality
document.addEventListener('DOMContentLoaded', function() {
    const event1Select = document.getElementById('event1-select');
    const event2Select = document.getElementById('event2-select');
    const compareBtn = document.getElementById('compare-btn');
    const chartContainer = document.getElementById('chart-container');
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const resetBtn = document.getElementById('reset-comparison');
    
    let chart = null;
    let completedEvents = [];

    // Get CSRF token for API requests
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                      document.querySelector('meta[name=csrf-token]')?.getAttribute('content');

    // Fetch completed events on page load
    fetchCompletedEvents();

    async function fetchCompletedEvents() { 
        try {
            showLoading(true, 'Loading events...');
            
            const response = await fetch('/api/completed-events/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            completedEvents = await response.json();
            
            if (completedEvents.length === 0) {
                showError('No completed events with evaluations found');
                return;
            }
            
            populateEventSelects();
            hideError();
            
        } catch (error) {
            console.error('Error fetching events:', error);
            showError('Failed to load events. Please refresh the page.');
        } finally {
            showLoading(false);
        }
    }

    function populateEventSelects() {
        const event1Options = completedEvents.map(event => 
            `<option value="${event.id}" data-title="${event.title}" data-date="${event.date}" data-responses="${event.response_count}">
                ${event.title}
            </option>`
        ).join('');
        
        const event2Options = completedEvents.map(event => 
            `<option value="${event.id}" data-title="${event.title}" data-date="${event.date}" data-responses="${event.response_count}">
                ${event.title}
            </option>`
        ).join('');

        event1Select.innerHTML = '<option value="">Select First Event</option>' + event1Options;
        event2Select.innerHTML = '<option value="">Select Second Event</option>' + event2Options;
    }

    // Event listeners
    event1Select.addEventListener('change', handleEventSelection);
    event2Select.addEventListener('change', handleEventSelection);
    compareBtn.addEventListener('click', compareEvents);
    resetBtn.addEventListener('click', resetComparison);

    function handleEventSelection() {
        updateEventInfo();
        updateCompareButton();
        hideChart();
    }

    function updateEventInfo() {
        updateSingleEventInfo('event1', event1Select.value, event1Select);
        updateSingleEventInfo('event2', event2Select.value, event2Select);
    }

    function updateSingleEventInfo(eventNum, eventId, selectElement) {
        const infoContainer = document.getElementById(`${eventNum}-info`);
        
        if (!eventId) {
            infoContainer.innerHTML = '<p class="no-selection">No event selected</p>';
            infoContainer.classList.remove('has-selection');
            return;
        }

        const selectedOption = selectElement.options[selectElement.selectedIndex];
        const eventTitle = selectedOption.getAttribute('data-title');
        const eventDate = selectedOption.getAttribute('data-date');
        const responseCount = selectedOption.getAttribute('data-responses');

        if (eventTitle) {
            infoContainer.innerHTML = `
                <div class="event-details">
                    <h5>${eventTitle}</h5>
                    <p><i class="bi bi-calendar-event"></i> ${eventDate}</p>
                    <p><i class="bi bi-people"></i> ${responseCount} responses</p>
                </div>
            `;
            infoContainer.classList.add('has-selection');
        }
    }

    function updateCompareButton() {
        const hasSelection = event1Select.value && event2Select.value;
        const isDifferent = event1Select.value !== event2Select.value;
        
        compareBtn.disabled = !(hasSelection && isDifferent);
        
        if (hasSelection && !isDifferent) {
            compareBtn.title = "Please select two different events";
        } else {
            compareBtn.title = "";
        }
    }

    async function compareEvents() {
        const event1Id = event1Select.value;
        const event2Id = event2Select.value;

        if (!event1Id || !event2Id || event1Id === event2Id) {
            alert('Please select two different events to compare');
            return;
        }

        showLoading(true, 'Comparing events...');
        hideError();
        hideChart();

        try {
            const [event1Data, event2Data] = await Promise.all([
                fetchEventData(event1Id),
                fetchEventData(event2Id)
            ]);
            
            if (!event1Data || !event2Data) {
                throw new Error('Failed to load event data');
            }
            
            showChart(event1Data, event2Data);
            
        } catch (error) {
            console.error('Error comparing events:', error);
            showError(error.message || 'Failed to load comparison data. Please try again.');
        } finally {
            showLoading(false);
        }
    }

    async function fetchEventData(eventId) {
        try {
            const response = await fetch(`/cal_event_data/${eventId}/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            const eventSelect = eventId === event1Select.value ? event1Select : event2Select;
            const selectedOption = Array.from(eventSelect.options).find(opt => opt.value === eventId);
            const eventTitle = selectedOption ? selectedOption.getAttribute('data-title') : `Event ${eventId}`;
            
            return {
                title: eventTitle,
                speaker: data.speaker || 0,
                venue: data.venue || 0,
                meals: data.meals || 0,
                manage: data.manage || 0,
                overall: data.overall || 0
            };
            
        } catch (error) {
            console.error(`Error fetching data for event ${eventId}:`, error);
            throw error;
        }
    }

    function showChart(event1Data, event2Data) {
        hideError();
        chartContainer.style.display = 'block';
        
        document.getElementById('event1-legend').textContent = event1Data.title;
        document.getElementById('event2-legend').textContent = event2Data.title;

        if (chart) {
            chart.destroy();
        }

        const labels = ['Speaker', 'Venue', 'Meals', 'Management', 'Overall'];
        const event1DataValues = [
            event1Data.speaker, 
            event1Data.venue, 
            event1Data.meals, 
            event1Data.manage, 
            event1Data.overall
        ];
        
        const event2DataValues = [
            event2Data.speaker, 
            event2Data.venue, 
            event2Data.meals, 
            event2Data.manage, 
            event2Data.overall
        ];

        const ctx = document.getElementById('comparison-chart').getContext('2d');
        chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: event1Data.title,
                        data: event1DataValues,
                        backgroundColor: 'rgba(59, 130, 246, 0.8)',
                        borderColor: '#1d4ed8',
                        borderWidth: 2,
                        borderRadius: 4
                    },
                    {
                        label: event2Data.title,
                        data: event2DataValues,
                        backgroundColor: 'rgba(239, 68, 68, 0.8)',
                        borderColor: '#dc2626',
                        borderWidth: 2,
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: `${event1Data.title} vs ${event2Data.title}`,
                        font: {
                            size: 16,
                            weight: '600'
                        },
                        padding: {
                            bottom: 20
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}/5.0`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 5,
                        ticks: {
                            stepSize: 0.5,
                            callback: function(value) {
                                return value.toFixed(1);
                            }
                        },
                        title: {
                            display: true,
                            text: 'Rating (1-5 scale)',
                            font: {
                                size: 12,
                                weight: '500'
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                }
            }
        });

        setTimeout(() => {
            chartContainer.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest' 
            });
        }, 100);
    }

    function resetComparison() {
        event1Select.value = '';
        event2Select.value = '';
        updateEventInfo();
        updateCompareButton();
        hideChart();
        hideError();
    }

    function showLoading(show, message = 'Loading...') {
        if (show) {
            loadingState.style.display = 'block';
            loadingState.querySelector('p').textContent = message;
        } else {
            loadingState.style.display = 'none';
        }
    }

    function hideChart() {
        chartContainer.style.display = 'none';
    }

    function showError(message) {
        errorState.querySelector('p').textContent = message;
        errorState.style.display = 'block';
    }

    function hideError() {
        errorState.style.display = 'none';
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            resetComparison();
        }
    });
});

// WEBINAR PAGINATION SYSTEM
document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const ITEMS_PER_PAGE = 6;
    
    // State management
    let allWebinars = [];
    let filteredWebinars = [];
    let currentPage = 1;
    let currentSearchTerm = '';
    let currentFilter = 'all'; // 'all', 'upcoming', 'past'
    
    // DOM elements
    const webinarList = document.getElementById('webinar-list');
    const searchInput = document.querySelector('.search-Input');
    const paginationContainer = document.getElementById('pagination');
    
    // Initialize the system
    setTimeout(initPagination, 500); // Delay to ensure DOM is ready
    
    function initPagination() {
        extractWebinarData();
        createFilterControls();
        setupEventListeners();
        applyFiltersAndSearch();
    }
    
function extractWebinarData() {
    const webinarCards = document.querySelectorAll('.webinar-card');
    allWebinars = Array.from(webinarCards).map((card, index) => {
        const title = card.querySelector('.webinar-title')?.textContent.trim() || '';
        const description = card.querySelector('p:not([class])')?.textContent.trim() || '';
        const dateText = card.querySelector('.bi-calendar')?.parentElement?.textContent || '';
        const timeText = card.querySelector('.bi-clock')?.parentElement?.textContent.replace(/^\s*\S+\s*/, '').trim() || '';
        const imgSrc = card.querySelector('.webinar-img')?.src || '';
        const detailLink = card.querySelector('.webinar-detail')?.href || '';
        
      
        const eventDate = parseEventDate(dateText);
        

       const now = new Date();
const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
const eventDateObj = new Date(eventDate); 

const isUpcoming = eventDateObj >= today;
        console.log(`Event: ${title}, Date: ${eventDate}, Upcoming: ${isUpcoming}`);

        return {
            id: index,
            title,
            description,
            dateText,
            timeText,
            imgSrc,
            detailLink,
            eventDate,
            isUpcoming,
            element: card.cloneNode(true)
        };
    });

    // Hide original cards
    webinarCards.forEach(card => card.style.display = 'none');
}

    
 function parseEventDate(dateStr) {
    try {
        
        let cleanDateStr = dateStr.replace(".", "").trim();

       
        let dateObj = new Date(cleanDateStr);

        if (isNaN(dateObj)) {
            throw new Error("Invalid date format");
        }

       
        let formatted = dateObj.toISOString().split("T")[0];
        return formatted;

    } catch (e) {
        console.warn('Could not parse date:', dateStr);
        return null; 
    }
}

    
    function createFilterControls() {
        const filterContainer = document.createElement('div');
        filterContainer.className = 'filter-controls';
        filterContainer.innerHTML = `
            <div class="filter-buttons">
                <button class="filter-btn active" data-filter="all">
                    <i class="bi bi-list"></i> All Events
                </button>
                <button class="filter-btn" data-filter="upcoming">
                    <i class="bi bi-calendar-plus"></i> Upcoming
                </button>
                <button class="filter-btn" data-filter="past">
                    <i class="bi bi-calendar-check"></i> Past Events
                </button>
            </div>
            <div class="results-info">
                <span id="results-count">0 events found</span>
            </div>
        `;
        
        const searchWrapper = document.querySelector('.search-wrapper');
        searchWrapper.parentNode.insertBefore(filterContainer, searchWrapper.nextSibling);
        addFilterStyles();
    }
    
    function addFilterStyles() {
        const styles = `
            .filter-controls {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 1rem 0;
                padding: 1rem;
                background: #f8f9fa;
                border-radius: 8px;
                flex-wrap: wrap;
                gap: 1rem;
            }
            
            .filter-buttons {
                display: flex;
                gap: 0.5rem;
                flex-wrap: wrap;
            }
            
            .filter-btn {
                padding: 0.5rem 1rem;
                border: 2px solid #dee2e6;
                background: white;
                color: #495057;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 0.9rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .filter-btn:hover {
                border-color: #007bff;
                color: #007bff;
                transform: translateY(-1px);
            }
            
            .filter-btn.active {
                background: #007bff;
                color: white;
                border-color: #007bff;
            }
            
            .results-info {
                color: #6c757d;
                font-size: 0.9rem;
            }
            
            .no-results {
                text-align: center;
                padding: 3rem;
                color: #6c757d;
            }
            
            .no-results i {
                font-size: 3rem;
                margin-bottom: 1rem;
                opacity: 0.5;
            }
            
            .pagination {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 0.5rem;
                margin: 2rem 0;
            }
            
            .pagination button {
                padding: 0.5rem 0.75rem;
                border: 1px solid #dee2e6;
                background: white;
                color: #495057;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .pagination button:hover:not(:disabled) {
                background: #e9ecef;
                border-color: #adb5bd;
            }
            
            .pagination button.active {
                background: #007bff;
                color: white;
                border-color: #007bff;
            }
            
            .pagination button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .page-info {
                margin: 0 1rem;
                color: #6c757d;
                font-size: 0.9rem;
            }
            
            @media (max-width: 768px) {
                .filter-controls {
                    flex-direction: column;
                    align-items: stretch;
                }
                
                .filter-buttons {
                    justify-content: center;
                }
                
                .results-info {
                    text-align: center;
                }
            }
        `;
        
        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }
    
    function setupEventListeners() {
        searchInput.addEventListener('input', debounce(handleSearch, 300));
        
        document.addEventListener('click', function(e) {
            if (e.target.matches('.filter-btn')) {
                handleFilterChange(e.target.dataset.filter);
            }
        });
        
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSearch();
            }
        });
    }
    
    function handleSearch() {
        currentSearchTerm = searchInput.value.toLowerCase().trim();
        currentPage = 1;
        applyFiltersAndSearch();
    }
    
    function handleFilterChange(filter) {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        
        currentFilter = filter;
        currentPage = 1;
        applyFiltersAndSearch();
    }
    
    function applyFiltersAndSearch() {
        let filtered = [...allWebinars];
        
        // Apply search filter
        if (currentSearchTerm) {
            filtered = filtered.filter(webinar => 
                webinar.title.toLowerCase().includes(currentSearchTerm) ||
                webinar.description.toLowerCase().includes(currentSearchTerm)
            );
        }
        
        // Apply date filter
        if (currentFilter === 'upcoming') {
            filtered = filtered.filter(webinar => webinar.isUpcoming);
        } else if (currentFilter === 'past') {
            filtered = filtered.filter(webinar => !webinar.isUpcoming);
        }
        
        filteredWebinars = filtered;
        updateResultsCount();
        renderWebinars();
        renderPagination();
    }
    
    function updateResultsCount() {
        const countElement = document.getElementById('results-count');
        const count = filteredWebinars.length;
        const filterText = currentFilter === 'all' ? 'events' : 
                          currentFilter === 'upcoming' ? 'upcoming events' : 'past events';
        
        countElement.textContent = `${count} ${filterText} found`;
    }
    
    function renderWebinars() {
        const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIndex = startIndex + ITEMS_PER_PAGE;
        const pageWebinars = filteredWebinars.slice(startIndex, endIndex);
        
        webinarList.innerHTML = '';
        
        if (pageWebinars.length === 0) {
            renderNoResults();
            return;
        }
        
        pageWebinars.forEach((webinar, index) => {
            const webinarElement = webinar.element.cloneNode(true);
            webinarElement.style.display = '';
            webinarElement.style.opacity = '0';
            webinarElement.style.transform = 'translateY(20px)';
            
            webinarList.appendChild(webinarElement);
            
            setTimeout(() => {
                webinarElement.style.transition = 'all 0.3s ease';
                webinarElement.style.opacity = '1';
                webinarElement.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }
    
    function renderNoResults() {
        const noResultsHtml = `
            <div class="col-12">
                <div class="no-results">
                    <i class="bi bi-search"></i>
                    <h4>No events found</h4>
                    <p>
                        ${currentSearchTerm ? 
                            `No events match "${currentSearchTerm}"` : 
                            `No ${currentFilter === 'all' ? '' : currentFilter} events available`
                        }
                    </p>
                    ${currentSearchTerm || currentFilter !== 'all' ? 
                        '<button onclick="clearFilters()" class="btn btn-primary">Clear filters</button>' : 
                        ''
                    }
                </div>
            </div>
        `;
        webinarList.innerHTML = noResultsHtml;
    }
    
    function renderPagination() {
        const totalPages = Math.ceil(filteredWebinars.length / ITEMS_PER_PAGE);
        
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }
        
        let paginationHtml = '<div class="pagination">';
        
        // Previous button
        paginationHtml += `
            <button ${currentPage === 1 ? 'disabled' : ''} onclick="goToPage(${currentPage - 1})">
                <i class="bi bi-chevron-left"></i> Previous
            </button>
        `;
        
        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        if (startPage > 1) {
            paginationHtml += `<button onclick="goToPage(1)">1</button>`;
            if (startPage > 2) {
                paginationHtml += '<span class="pagination-ellipsis">...</span>';
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <button class="${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">
                    ${i}
                </button>
            `;
        }
        
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationHtml += '<span class="pagination-ellipsis">...</span>';
            }
            paginationHtml += `<button onclick="goToPage(${totalPages})">${totalPages}</button>`;
        }
        
        // Next button
        paginationHtml += `
            <button ${currentPage === totalPages ? 'disabled' : ''} onclick="goToPage(${currentPage + 1})">
                Next <i class="bi bi-chevron-right"></i>
            </button>
        `;
        
        // Page info
        const startItem = Math.min((currentPage - 1) * ITEMS_PER_PAGE + 1, filteredWebinars.length);
        const endItem = Math.min(currentPage * ITEMS_PER_PAGE, filteredWebinars.length);
        
        paginationHtml += `
            <div class="page-info">
                Showing ${startItem}-${endItem} of ${filteredWebinars.length} events
            </div>
        `;
        
        paginationHtml += '</div>';
        paginationContainer.innerHTML = paginationHtml;
    }
    
    // Global functions for pagination controls
    window.goToPage = function(page) {
        currentPage = page;
        renderWebinars();
        renderPagination();
        webinarList.scrollIntoView({ behavior: 'smooth' });
    };
    
    window.clearFilters = function() {
        searchInput.value = '';
        currentSearchTerm = '';
        currentFilter = 'all';
        currentPage = 1;
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === 'all');
        });
        
        applyFiltersAndSearch();
    };
    
    // Utility function for debouncing search
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Add keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.target === searchInput) return;
        
        switch(e.key) {
            case 'ArrowLeft':
                if (currentPage > 1) {
                    e.preventDefault();
                    goToPage(currentPage - 1);
                }
                break;
            case 'ArrowRight':
                const totalPages = Math.ceil(filteredWebinars.length / ITEMS_PER_PAGE);
                if (currentPage < totalPages) {
                    e.preventDefault();
                    goToPage(currentPage + 1);
                }
                break;
        }
    });
    
    // Enhanced search functionality
    setTimeout(() => {
        const searchContainer = document.querySelector('.search-cont');
        if (searchContainer) {
            searchContainer.style.position = 'relative';
            
            searchInput.addEventListener('focus', function() {
                this.parentElement.style.borderColor = '#007bff';
                this.parentElement.style.boxShadow = '0 0 0 0.2rem rgba(0,123,255,.25)';
            });
            
            searchInput.addEventListener('blur', function() {
                this.parentElement.style.borderColor = '';
                this.parentElement.style.boxShadow = '';
            });
        }
    }, 600);
});

// Additional CSS for enhanced UI
const additionalPaginationCSS = `
.error-state p {
    font-size: 0.95rem;
    line-height: 1.5;
}

.loading-state p {
    font-size: 0.95rem;
    color: #6b7280;
    margin: 0;
}

.compare-btn[disabled] {
    opacity: 0.6;
    cursor: not-allowed;
}

.event-select option {
    padding: 0.5rem;
}

.chart-container {
    animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.search-Input:focus {
    outline: none;
}

.pagination-ellipsis {
    padding: 0.5rem 0.75rem;
    color: #6c757d;
}

.btn {
    padding: 0.375rem 0.75rem;
    margin-bottom: 0;
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.5;
    color: #495057;
    text-align: center;
    text-decoration: none;
    vertical-align: middle;
    cursor: pointer;
    user-select: none;
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 0.25rem;
    transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.btn-primary {
    color: #fff;
    background-color: #007bff;
    border-color: #007bff;
}

.btn-primary:hover {
    color: #fff;
    background-color: #0069d9;
    border-color: #0062cc;
}
`;

// Inject additional CSS
const paginationStyle = document.createElement('style');
paginationStyle.textContent = additionalPaginationCSS;
document.head.appendChild(paginationStyle);