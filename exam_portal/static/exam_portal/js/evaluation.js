
// Store chart instances and data globally
let chartInstances = {};
let chartData = {};
let testChartInstances = {};
let testData = {};

// Attendees data management
let attendeesData = [];
let filteredAttendeesData = [];
let currentAttendeesPage = 1;
let attendeesRowsPerPage = 10;

document.addEventListener("DOMContentLoaded", ()=>{
    console.log("js is connected")
    window.alert("js is connected")
})


// Your existing chart functions remain the same...
async function DownloadExcel() {
    const id = parseInt("{{ webinar.id }}");
    const response = await fetch(`/exam_portal/result_data/${id}`);
    const data = await response.json();

    console.log("Data fetched:", data);

    let csvContent = "";

    // ===== EVALUATION DATA SHEET =====
    csvContent += "=== EVALUATION DATA ===\n";
    csvContent += "Email,Deped ID,Sex,Timestamp,Speaker,Venue,Meal,Manage\n";

    const maxEvalLength = Math.max(
        data.email?.length || 0,
        data.deped_id?.length || 0,
        data.sex?.length || 0,
        data.timestamp?.length || 0,
        data.speaker?.length || 0,
        data.venue?.length || 0,
        data.meal?.length || 0,
        data.manage?.length || 0
    );

    for (let i = 0; i < maxEvalLength; i++) {
        const email = data.email?.[i] ?? "";
        const schoolId = data.deped_id?.[i] ?? "";
        const sex = data.sex?.[i] ?? "";
        const timestamp = data.timestamp?.[i] ?? "";
        const speaker = data.speaker?.[i] ?? "";
        const venue = data.venue?.[i] ?? "";
        const meal = data.meal?.[i] ?? "";
        const manage = data.manage?.[i] ?? "";

        const escapedEmail = email.includes(',') ? `"${email}"` : email;
        const escapedSchoolId = schoolId.includes(',') ? `"${schoolId}"` : schoolId;
        const escapedSex = sex.includes(',') ? `"${sex}"` : sex;
        const escapedTimestamp = timestamp.includes(',') ? `"${timestamp}"` : timestamp;

        csvContent += `${escapedEmail},${escapedSchoolId},${escapedSex},${escapedTimestamp},${speaker},${venue},${meal},${manage}\n`;
    }

    // Add attendees data
    csvContent += "\n=== ATTENDEES DATA ===\n";
    csvContent += "Email,DepEd ID,Attendance Score,Completion Time\n";
    
    const maxAttendanceLength = Math.max(
        data.attendance_emails?.length || 0,
        data.attendance_deped_ids?.length || 0,
        data.attendance_scores?.length || 0
    );

    for (let i = 0; i < maxAttendanceLength; i++) {
        const email = data.attendance_emails?.[i] ?? "";
        const depedId = data.attendance_deped_ids?.[i] ?? "";
        const score = data.attendance_scores?.[i] ?? "";
        
        csvContent += `${email},${depedId},${score},\n`;
    }

    // Add comments data
    csvContent += "\n=== COMMENTS DATA ===\n";
    csvContent += "Email,DepEd ID,Comment,Timestamp\n";
    
    const maxCommentsLength = Math.max(
        data.comment_emails?.length || 0,
        data.comment_deped_ids?.length || 0,
        data.comment_texts?.length || 0,
        data.comment_timestamps?.length || 0
    );

    for (let i = 0; i < maxCommentsLength; i++) {
        const email = data.comment_emails?.[i] ?? "";
        const depedId = data.comment_deped_ids?.[i] ?? "";
        const text = data.comment_texts?.[i] ?? "";
        const timestamp = data.comment_timestamps?.[i] ?? "";
        
        const escapedEmail = email.includes(',') ? `"${email}"` : email;
        const escapedText = text.includes(',') ? `"${text.replace(/"/g, '""')}"` : text;
        
        csvContent += `${escapedEmail},${depedId},${escapedText},${timestamp}\n`;
    }

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `webinar_complete_data_${id}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

async function downloadTestData() {
    console.log("Downloading test data...");
    const response = await fetch("{% url 'test_data' webinar.id %}");
    const data = await response.json();

    console.log("Fetched test data:", data);

    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.json_to_sheet(data.test_result);
    XLSX.utils.book_append_sheet(workbook, worksheet, "test_data");
    XLSX.writeFile(workbook, "Test_result.xlsx");
}

// Attendees table functions
function displayAttendeesTable() {
    const tableBody = document.getElementById('attendees-table-body');
    const tableInfo = document.getElementById('attendees-table-info');
    
    tableBody.innerHTML = "";
    
    if (filteredAttendeesData.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No attendees data available</td></tr>';
        tableInfo.innerHTML = "Showing 0 entries";
        return;
    }
    
    let start = (currentAttendeesPage - 1) * attendeesRowsPerPage;
    let end = start + attendeesRowsPerPage;
    let paginatedData = filteredAttendeesData.slice(start, end);
    
    paginatedData.forEach((attendee, index) => {
        let statusClass, statusText, progressBar;
        
        if (attendee.attendance >= 80) {
            statusClass = 'attendance-completed';
            statusText = 'Completed';
        } else if (attendee.attendance > 0) {
            statusClass = 'attendance-partial';
            statusText = 'In Progress';
        } else {
            statusClass = 'attendance-not-started';
            statusText = 'Not Started';
        }
        
        progressBar = `
            <div class="progress" style="height: 20px;">
                <div class="progress-bar bg-${attendee.attendance >= 80 ? 'success' : attendee.attendance > 0 ? 'warning' : 'danger'}" 
                     role="progressbar" 
                     style="width: ${attendee.attendance}%"
                     aria-valuenow="${attendee.attendance}" 
                     aria-valuemin="0" 
                     aria-valuemax="100">
                    ${attendee.attendance}%
                </div>
            </div>
        `;
        
        let tr = `<tr>
                    <td>${start + index + 1}</td>
                    <td title="${attendee.email}">${attendee.email}</td>
                    <td>${attendee.deped_id || 'N/A'}</td>
                    <td><span class="attendance-badge ${statusClass}">${statusText}</span></td>
                    <td>${progressBar}</td>
                    <td>${attendee.completion_time || 'Not completed'}</td>
                  </tr>`;
        tableBody.innerHTML += tr;
    });
    
    let actualEnd = Math.min(end, filteredAttendeesData.length);
    tableInfo.innerHTML = `Showing ${start + 1} to ${actualEnd} of ${filteredAttendeesData.length} entries`;
}

function setupAttendeesPagination() {
    const pagination = document.getElementById('attendees-pagination');
    pagination.innerHTML = "";
    
    if (filteredAttendeesData.length === 0) return;
    
    let pageCount = Math.ceil(filteredAttendeesData.length / attendeesRowsPerPage);
    
    // Previous button
    let prevLi = document.createElement("li");
    prevLi.className = `page-item ${currentAttendeesPage === 1 ? "disabled" : ""}`;
    prevLi.innerHTML = '<a class="page-link" href="#"><i class="fas fa-chevron-left"></i></a>';
    if (currentAttendeesPage > 1) {
        prevLi.addEventListener("click", function(e) {
            e.preventDefault();
            currentAttendeesPage--;
            displayAttendeesTable();
            setupAttendeesPagination();
        });
    }
    pagination.appendChild(prevLi);
    
    // Page numbers
    let startPage = Math.max(1, currentAttendeesPage - 2);
    let endPage = Math.min(pageCount, currentAttendeesPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        let li = document.createElement("li");
        li.className = "page-item " + (i === currentAttendeesPage ? "active" : "");
        li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        
        li.addEventListener("click", function(e) {
            e.preventDefault();
            currentAttendeesPage = i;
            displayAttendeesTable();
            setupAttendeesPagination();
        });
        
        pagination.appendChild(li);
    }
    
    // Next button
    let nextLi = document.createElement("li");
    nextLi.className = `page-item ${currentAttendeesPage === pageCount ? "disabled" : ""}`;
    nextLi.innerHTML = '<a class="page-link" href="#"><i class="fas fa-chevron-right"></i></a>';
    if (currentAttendeesPage < pageCount) {
        nextLi.addEventListener("click", function(e) {
            e.preventDefault();
            currentAttendeesPage++;
            displayAttendeesTable();
            setupAttendeesPagination();
        });
    }
    pagination.appendChild(nextLi);
}

function searchAttendees() {
    const searchInput = document.getElementById('attendees-search');
    const searchTerm = searchInput.value.toLowerCase();
    
    if (searchTerm === '') {
        filteredAttendeesData = attendeesData;
    } else {
        filteredAttendeesData = attendeesData.filter(item =>
            item.email.toLowerCase().includes(searchTerm) ||
            (item.deped_id && item.deped_id.toLowerCase().includes(searchTerm))
        );
    }
    
    currentAttendeesPage = 1;
    displayAttendeesTable();
    setupAttendeesPagination();
}

function changeAttendeesRowsPerPage() {
    const select = document.getElementById('attendees-rows-select');
    attendeesRowsPerPage = parseInt(select.value);
    currentAttendeesPage = 1;
    displayAttendeesTable();
    setupAttendeesPagination();
}

// Comments carousel functions
function setupCommentsCarousel(commentsData) {
    const indicatorsContainer = document.getElementById('comment-indicators');
    const slidesContainer = document.getElementById('comment-slides');
    
    if (!commentsData || commentsData.length === 0) {
        slidesContainer.innerHTML = `
            <div class="carousel-item active">
                <div class="no-comments">
                    <i class="fas fa-comments" style="font-size: 48px; margin-bottom: 1rem; color: #dee2e6;"></i>
                    <h5>No Comments Yet</h5>
                    <p>No participant comments are available for this webinar.</p>
                </div>
            </div>
        `;
        indicatorsContainer.innerHTML = '';
        return;
    }
    
    // Clear existing content
    indicatorsContainer.innerHTML = '';
    slidesContainer.innerHTML = '';
    
    // Create indicators and slides
    commentsData.forEach((comment, index) => {
        // Create indicator
        const indicator = document.createElement('button');
        indicator.type = 'button';
        indicator.setAttribute('data-bs-target', '#commentsCarousel');
        indicator.setAttribute('data-bs-slide-to', index.toString());
        indicator.className = index === 0 ? 'active' : '';
        indicator.setAttribute('aria-current', index === 0 ? 'true' : 'false');
        indicator.setAttribute('aria-label', `Slide ${index + 1}`);
        indicatorsContainer.appendChild(indicator);
        
        // Create slide
        const slide = document.createElement('div');
        slide.className = `carousel-item ${index === 0 ? 'active' : ''}`;
        
        // Get user initials for avatar
        const userInitials = comment.user_email ? 
            comment.user_email.split('@')[0].slice(0, 2).toUpperCase() : 
            'AN';
        
        slide.innerHTML = `
            <div class="comment-card">
                <div class="comment-header">
                    <div class="comment-avatar">
                        ${userInitials}
                    </div>
                    <div class="comment-user-info">
                        <h6>${comment.user_email || 'Anonymous'}</h6>
                        <small>DepEd ID: ${comment.deped_id || 'N/A'}</small>
                    </div>
                </div>
                <div class="comment-text">
                    ${comment.text || 'No comment text available'}
                </div>
                <div class="comment-footer mt-3">
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i>
                        ${comment.timestamp || 'No timestamp'}
                    </small>
                </div>
            </div>
        `;
        
        slidesContainer.appendChild(slide);
    });
}

// Chart functions (keeping your existing chart code)
function hasData(data) {
    if (!Array.isArray(data)) return false;
    return data.some(value => value > 0);
}

function showNoDataMessage(chartId) {
    const canvas = document.getElementById(chartId);
    const noDataDiv = document.getElementById(chartId + '-no-data');
    
    if (canvas) canvas.style.display = 'none';
    if (noDataDiv) noDataDiv.style.display = 'flex';
}

function hideNoDataMessage(chartId) {
    const canvas = document.getElementById(chartId);
    const noDataDiv = document.getElementById(chartId + '-no-data');
    
    if (canvas) canvas.style.display = 'block';
    if (noDataDiv) noDataDiv.style.display = 'none';
}

function createChart(chartId, type, data, labels, colors, title) {
    if (chartInstances[chartId]) {
        chartInstances[chartId].destroy();
    }

    if (!hasData(data)) {
        showNoDataMessage(chartId);
        return;
    }

    hideNoDataMessage(chartId);
    
    const ctx = document.getElementById(chartId).getContext('2d');
    
    const config = {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: type === 'bar' ? colors : '#fff',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: type === 'bar' ? 'top' : 'right',
                    labels: {
                        boxWidth: 12,
                        padding: 20
                    }
                },
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 14
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                }
            }
        }
    };

    if (type === 'bar') {
        config.options.scales = {
            y: {
                beginAtZero: true,
                ticks: {
                    stepSize: 1
                }
            }
        };
    }

    chartInstances[chartId] = new Chart(ctx, config);
}

function createTestChart(chartId, type, data, labels) {
    if (testChartInstances[chartId]) {
        testChartInstances[chartId].destroy();
    }

    if (!hasData(Object.values(data))) {
        showNoDataMessage(chartId);
        return;
    }

    hideNoDataMessage(chartId);
    
    const ctx = document.getElementById(chartId).getContext('2d');
    const backgroundColor = labels.map(() => randomColor());
    
    const config = {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                label: "Number of students",
                data: Object.values(data),
                backgroundColor: backgroundColor,
                borderColor: type === 'bar' ? backgroundColor : '#fff',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: type === 'bar' ? 'top' : 'right'
                }
            }
        }
    };

    if (type === 'bar') {
        config.options.scales = {
            y: {
                beginAtZero: true,
                ticks: {
                    stepSize: 1
                }
            }
        };
    }

    testChartInstances[chartId] = new Chart(ctx, config);
}

function changeChartType(chartId, newType) {
    // Update active button
    const buttons = document.querySelectorAll(`[onclick*="'${chartId}'"]`);
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    const labels = ['5 (Excellent)', '4 (Good)', '3 (Average)', '2 (Poor)', '1 (Very Poor)'];
    const colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336'];
    const title = chartId.charAt(0).toUpperCase() + chartId.slice(1) + ' Evaluation';

    createChart(chartId, newType, chartData[chartId], labels, colors, title);
}

function changeTestChartType(chartId, newType) {
    // Update active button
    const buttons = document.querySelectorAll(`[onclick*="'${chartId}'"]`);
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    const labels = Object.keys(testData[chartId] || {});
    createTestChart(chartId, newType, testData[chartId], labels);
}

function randomColor() {
    const hue = Math.floor(Math.random() * 360);
    const saturation = 50 + Math.random() * 10;    
    const lightness = 45 + Math.random() * 10;     
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    async function fetchData() {
        const id = parseInt("{{ webinar.id }}");
        const evaluation = await fetch(`/exam_portal/rounded_data/${id}`);
        const data = await evaluation.json();
                
        chartData = {
            speaker: data.speaker,
            venue: data.venue,
            food: data.meals,
            manage: data.manage,
            overall: data.overall
        };
                
        const labels = ['5 (Excellent)', '4 (Good)', '3 (Average)', '2 (Poor)', '1 (Very Poor)'];
        const colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336'];
                
        const chartIds = ['speaker', 'venue', 'food', 'manage', 'overall'];
                
        chartIds.forEach(id => {
            const title = id.charAt(0).toUpperCase() + id.slice(1) + ' Evaluation';
            createChart(id, 'pie', chartData[id], labels, colors, title);
        });
    }
    
    // Initialize test charts
    async function TestChart() {
        const graphIds = ['pre-test', 'post-test'];
        const pre_test = "{% url 'test_score' webinar.id 'pre_test' %}";
        const post_test = "{% url 'test_score' webinar.id 'post_test' %}";

        for (const [index, id] of graphIds.entries()) {
            const url = (index < 1) ? pre_test : post_test;
            
            const response = await fetch(url);
            const json = await response.json();
            console.log("Data JSON:", json);
            
            testData[id] = json.scores;
            const labels = Object.keys(json.scores);
            
            createTestChart(id, 'doughnut', json.scores, labels);
        }
    }

    // Initialize attendees and comments data
    async function fetchAttendeesAndComments() {
        const id = parseInt("{{ webinar.id }}");
        const response = await fetch(`/exam_portal/result_data/${id}`);
        const data = await response.json();
        
        // Setup attendees data
        attendeesData = [];
        const maxLength = Math.max(
            data.attendance_emails?.length || 0,
            data.attendance_deped_ids?.length || 0,
            data.attendance_scores?.length || 0
        );
        
        for (let i = 0; i < maxLength; i++) {
            attendeesData.push({
                email: data.attendance_emails?.[i] || '',
                deped_id: data.attendance_deped_ids?.[i] || '',
                attendance: data.attendance_scores?.[i] || 0,
                completion_time: null // You may need to add this to your backend data
            });
        }
        
        filteredAttendeesData = [...attendeesData];
        displayAttendeesTable();
        setupAttendeesPagination();
        
        // Setup comments data
        const commentsData = [];
        const maxCommentsLength = Math.max(
            data.comment_emails?.length || 0,
            data.comment_deped_ids?.length || 0,
            data.comment_texts?.length || 0,
            data.comment_timestamps?.length || 0
        );
        
        for (let i = 0; i < maxCommentsLength; i++) {
            commentsData.push({
                user_email: data.comment_emails?.[i] || '',
                deped_id: data.comment_deped_ids?.[i] || '',
                text: data.comment_texts?.[i] || '',
                timestamp: data.comment_timestamps?.[i] || ''
            });
        }
        
        setupCommentsCarousel(commentsData);
    }
    
    // Initialize all components
    fetchData();
    TestChart();
    fetchAttendeesAndComments();
});
