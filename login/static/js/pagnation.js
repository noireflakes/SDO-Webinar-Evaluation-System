// Webinar Pagination System with Search and Filtering
document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const ITEMS_PER_PAGE = 6; // Adjust based on your needs
    
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
    init();
    
    function init() {
        // Extract webinar data from existing DOM
        extractWebinarData();
        
        // Create filter controls
        createFilterControls();
        
        // Set up event listeners
        setupEventListeners();
        
        // Initial render
        applyFiltersAndSearch();
    }
    
    function extractWebinarData() {
        const webinarCards = document.querySelectorAll('.webinar-card');
        allWebinars = Array.from(webinarCards).map((card, index) => {
            // Extract data from the card
            const title = card.querySelector('.webinar-title')?.textContent.trim() || '';
            const description = card.querySelector('p:not([class])')?.textContent.trim() || '';
            const dateText = card.querySelector('.bi-calendar')?.parentElement?.textContent.replace(/^\s*\S+\s*/, '').trim() || '';
            const timeText = card.querySelector('.bi-clock')?.parentElement?.textContent.replace(/^\s*\S+\s*/, '').trim() || '';
            const imgSrc = card.querySelector('.webinar-img')?.src || '';
            const detailLink = card.querySelector('.webinar-detail')?.href || '';
            
            // Parse date for filtering
            const eventDate = parseEventDate(dateText);
            const now = new Date();
            const isUpcoming = eventDate > now;
            
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
                element: card.cloneNode(true) // Store the original element
            };
        });
        
        // Hide original cards
        webinarCards.forEach(card => card.style.display = 'none');
    }
    
    function parseEventDate(dateStr) {
        // Try to parse the date string
        // Adjust this function based on your date format
        try {
            // Handle various date formats
            const cleanDate = dateStr.replace(/^\s*\S+\s*/, '').trim();
            return new Date(cleanDate);
        } catch (e) {
            console.warn('Could not parse date:', dateStr);
            return new Date(); // Default to current date
        }
    }
    
    function createFilterControls() {
        // Create filter container
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
        
        // Insert filter controls before the webinar list
        const searchWrapper = document.querySelector('.search-wrapper');
        searchWrapper.parentNode.insertBefore(filterContainer, searchWrapper.nextSibling);
        
        // Add CSS for filter controls
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
        // Search input
        searchInput.addEventListener('input', debounce(handleSearch, 300));
        
        // Filter buttons
        document.addEventListener('click', function(e) {
            if (e.target.matches('.filter-btn')) {
                handleFilterChange(e.target.dataset.filter);
            }
        });
        
        // Enhanced search - also listen for Enter key
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSearch();
            }
        });
    }
    
    function handleSearch() {
        currentSearchTerm = searchInput.value.toLowerCase().trim();
        currentPage = 1; // Reset to first page
        applyFiltersAndSearch();
    }
    
    function handleFilterChange(filter) {
        // Update filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        
        currentFilter = filter;
        currentPage = 1; // Reset to first page
        applyFiltersAndSearch();
    }
    
    function applyFiltersAndSearch() {
        // Start with all webinars
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
        // Calculate pagination
        const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIndex = startIndex + ITEMS_PER_PAGE;
        const pageWebinars = filteredWebinars.slice(startIndex, endIndex);
        
        // Clear existing content
        webinarList.innerHTML = '';
        
        if (pageWebinars.length === 0) {
            renderNoResults();
            return;
        }
        
        // Render webinars for current page
        pageWebinars.forEach((webinar, index) => {
            const webinarElement = webinar.element.cloneNode(true);
            webinarElement.style.display = '';
            
            // Add animation delay for staggered effect
            webinarElement.style.opacity = '0';
            webinarElement.style.transform = 'translateY(20px)';
            
            webinarList.appendChild(webinarElement);
            
            // Animate in
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
        
        // Scroll to top of webinar list
        webinarList.scrollIntoView({ behavior: 'smooth' });
    };
    
    window.clearFilters = function() {
        searchInput.value = '';
        currentSearchTerm = '';
        currentFilter = 'all';
        currentPage = 1;
        
        // Reset filter buttons
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
        if (e.target === searchInput) return; // Don't interfere with search input
        
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
    
    // Add URL parameter support (optional)
    function updateURL() {
        const params = new URLSearchParams();
        if (currentSearchTerm) params.set('search', currentSearchTerm);
        if (currentFilter !== 'all') params.set('filter', currentFilter);
        if (currentPage > 1) params.set('page', currentPage);
        
        const newURL = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
        history.replaceState(null, '', newURL);
    }
    
    function loadFromURL() {
        const params = new URLSearchParams(window.location.search);
        
        if (params.has('search')) {
            currentSearchTerm = params.get('search');
            searchInput.value = currentSearchTerm;
        }
        
        if (params.has('filter')) {
            currentFilter = params.get('filter');
        }
        
        if (params.has('page')) {
            currentPage = parseInt(params.get('page')) || 1;
        }
        
        // Update filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === currentFilter);
        });
    }
    
    // Load initial state from URL
    setTimeout(() => {
        loadFromURL();
        applyFiltersAndSearch();
    }, 100);
});

// Enhanced search functionality
function enhanceSearchBar() {
    const searchInput = document.querySelector('.search-Input');
    const searchContainer = document.querySelector('.search-cont');
    
    // Add search suggestions (optional)
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.className = 'search-suggestions';
    suggestionsContainer.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #ddd;
        border-top: none;
        border-radius: 0 0 4px 4px;
        max-height: 200px;
        overflow-y: auto;
        z-index: 1000;
        display: none;
    `;
    
    searchContainer.style.position = 'relative';
    searchContainer.appendChild(suggestionsContainer);
    
    // Add placeholder text
    searchInput.placeholder = 'Search events by title or description...';
    
    // Enhanced search with highlighting
    searchInput.addEventListener('focus', function() {
        this.parentElement.style.borderColor = '#007bff';
        this.parentElement.style.boxShadow = '0 0 0 0.2rem rgba(0,123,255,.25)';
    });
    
    searchInput.addEventListener('blur', function() {
        this.parentElement.style.borderColor = '';
        this.parentElement.style.boxShadow = '';
        
        // Hide suggestions after a delay to allow clicking
        setTimeout(() => {
            suggestionsContainer.style.display = 'none';
        }, 200);
    });
}

// Initialize enhanced search
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(enhanceSearchBar, 500);
});