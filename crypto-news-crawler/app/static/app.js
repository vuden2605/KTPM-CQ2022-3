// Global variables
let allNews = [];
let currentPage = 1;
let totalPages = 1;
let itemsPerPage = 12;
let totalNewsCount = 0;
let currentFilters = {
    search: '',
    source: '',
    sentiment: '',
    fromDate: '',
    toDate: '',
    symbol: ''
};
const newsModal = new bootstrap.Modal(document.getElementById('newsModal'));

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    loadNews();
    setupAutoRefresh();
});

/**
 * Load news from API
 */
async function loadNews(page = 1) {
    try {
        currentPage = page;
        const offset = (page - 1) * itemsPerPage;
        
        // Show loading state
        const container = document.getElementById('newsContainer');
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Đang tải...</span>
                </div>
                <p class="mt-3">Đang tải tin tức...</p>
            </div>
        `;
        
        // Build query parameters
        const params = new URLSearchParams({
            limit: itemsPerPage,
            offset: offset
        });
        
        if (currentFilters.source) params.append('source', currentFilters.source);
        if (currentFilters.sentiment) params.append('sentiment', currentFilters.sentiment);
        if (currentFilters.search) params.append('search', currentFilters.search);
        if (currentFilters.fromDate) params.append('from_date', currentFilters.fromDate);
        if (currentFilters.toDate) params.append('to_date', currentFilters.toDate);
        if (currentFilters.symbol) params.append('symbol', currentFilters.symbol);
        
        // Build count parameters
        const countParams = new URLSearchParams();
        if (currentFilters.source) countParams.append('source', currentFilters.source);
        if (currentFilters.sentiment) countParams.append('sentiment', currentFilters.sentiment);
        if (currentFilters.search) countParams.append('search', currentFilters.search);
        if (currentFilters.fromDate) countParams.append('from_date', currentFilters.fromDate);
        if (currentFilters.toDate) countParams.append('to_date', currentFilters.toDate);
        if (currentFilters.symbol) countParams.append('symbol', currentFilters.symbol);
        
        // Fetch news and total count in parallel
        const [newsResponse, countResponse] = await Promise.all([
            fetch(`/api/news?${params.toString()}`),
            fetch(`/api/news/count?${countParams.toString()}`)
        ]);
        
        if (!newsResponse.ok || !countResponse.ok) {
            throw new Error(`HTTP error!`);
        }
        
        const data = await newsResponse.json();
        const countData = await countResponse.json();
        
        allNews = data;
        totalNewsCount = countData.total;
        totalPages = Math.ceil(totalNewsCount / itemsPerPage);
        
        displayNews(allNews);
        updateStats();
        createPagination();
        updateFilterDisplay();
        
    } catch (error) {
        console.error('Error loading news:', error);
        showErrorState('Không thể tải tin tức. Vui lòng thử lại sau.');
    }
}

/**
 * Display news on page
 */
function displayNews(newsArray) {
    const container = document.getElementById('newsContainer');
    
    if (newsArray.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <h5>Không có tin tức nào</h5>
                    <p>Không tìm thấy tin tức phù hợp với tiêu chí tìm kiếm của bạn.</p>
                </div>
            </div>
        `;
        return;
    }
    
    container.innerHTML = newsArray.map(news => createNewsCard(news)).join('');
    
    // Add click listeners
    document.querySelectorAll('.news-card').forEach(card => {
        card.addEventListener('click', function() {
            const newsId = this.dataset.newsId;
            const newsItem = allNews.find(n => n.id === newsId);
            if (newsItem) {
                showNewsDetail(newsItem);
            }
        });
    });
}

/**
 * Create news card HTML
 */
function createNewsCard(news) {
    const date = new Date(news.published_at);
    const formattedDate = formatDate(date);
    const sentimentClass = getSentimentClass(news.sentiment_label);
    const sentimentLabel = getSentimentLabel(news.sentiment_label);
    const symbols = Array.isArray(news.symbols) ? news.symbols : [];
    const symbolsText = symbols.length ? symbols.join(', ') : '';
    
    return `
        <div class="col-lg-4 col-md-6">
            <div class="news-card" data-news-id="${news.id}">
                <div class="news-card-image">
                    <i class="fas fa-newspaper"></i>
                </div>
                <div class="news-card-body">
                    <span class="news-source-badge">${capitalizeSource(news.source)}</span>
                    <h3 class="news-card-title">${news.title}</h3>
                    <p class="news-card-summary">${news.content || 'Không có mô tả'}</p>
                    <div class="news-card-meta">
                        <span class="news-card-date">
                            <i class="fas fa-calendar-alt"></i>
                            ${formattedDate}
                        </span>
                        <div class="d-flex flex-column align-items-end text-end">
                            ${symbolsText ? `<span class="news-symbols small mb-1"><i class="fas fa-coins me-1"></i>${symbolsText}</span>` : ''}
                            ${news.sentiment_label ? `<span class="sentiment-badge sentiment-${sentimentClass}">${sentimentLabel}</span>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Show news detail in modal
 */
function showNewsDetail(news) {
    document.getElementById('newsModalTitle').textContent = news.title;
    
    const contentHtml = `
        <div class="news-detail">
            <div class="mb-3">
                <span class="badge bg-primary">${capitalizeSource(news.source)}</span>
                <span class="badge bg-secondary ms-2">${news.language}</span>
            </div>
            ${Array.isArray(news.symbols) && news.symbols.length ? `
            <p><strong>Đồng liên quan:</strong> ${news.symbols.join(', ')}</p>
            ` : ''}

            ${news.author ? `<p><strong>Tác giả:</strong> ${news.author}</p>` : ''}
            
            ${news.published_at ? `
                <p><strong>Ngày xuất bản:</strong> ${formatDateTime(new Date(news.published_at))}</p>
            ` : ''}

            ${news.content ? `
                <div class="mt-4">
                    <h6>Nội dung</h6>
                    <p>${news.content}</p>
                </div>
            ` : ''}
            
            ${news.sentiment_label ? `
                <div class="mt-4">
                    <h6>Phân tích cảm xúc</h6>
                    <p>
                        Cảm xúc: <strong>${getSentimentLabel(news.sentiment_label)}</strong><br>
                        Điểm số: <strong>${(news.sentiment_score * 100).toFixed(1)}%</strong>
                    </p>
                </div>
            ` : ''}
        </div>
    `;
    
    document.getElementById('newsModalContent').innerHTML = contentHtml;
    document.getElementById('newsModalLink').href = news.url;
    newsModal.show();
}

/**
 * Filter news based on search and filters
 */
let filterTimeout;
function filterNews() {
    // Clear previous timeout
    if (filterTimeout) {
        clearTimeout(filterTimeout);
    }
    
    // Debounce for search input (wait 500ms after user stops typing)
    filterTimeout = setTimeout(() => {
        // Update current filters
        currentFilters.search = document.getElementById('searchInput').value.trim();
        currentFilters.source = document.getElementById('sourceFilter').value;
        currentFilters.sentiment = document.getElementById('sentimentFilter').value;
        currentFilters.fromDate = document.getElementById('fromDate').value;
        currentFilters.toDate = document.getElementById('toDate').value;
        currentFilters.symbol = document.getElementById('symbolFilter') ? document.getElementById('symbolFilter').value.trim().toUpperCase() : '';
        
        // Reset to page 1 and reload
        loadNews(1);
    }, 500);
}

/**
 * Filter news immediately (for dropdowns)
 */
function filterNewsImmediate() {
    // Update current filters
    currentFilters.search = document.getElementById('searchInput').value.trim();
    currentFilters.source = document.getElementById('sourceFilter').value;
    currentFilters.sentiment = document.getElementById('sentimentFilter').value;
    currentFilters.fromDate = document.getElementById('fromDate').value;
    currentFilters.toDate = document.getElementById('toDate').value;
    currentFilters.symbol = document.getElementById('symbolFilter') ? document.getElementById('symbolFilter').value.trim().toUpperCase() : '';
    
    // Reset to page 1 and reload
    loadNews(1);
}

/**
 * Clear all filters
 */
function clearFilters() {
    // Clear input fields
    document.getElementById('searchInput').value = '';
    document.getElementById('sourceFilter').value = '';
    document.getElementById('sentimentFilter').value = '';
    if (document.getElementById('fromDate')) document.getElementById('fromDate').value = '';
    if (document.getElementById('toDate')) document.getElementById('toDate').value = '';
    if (document.getElementById('symbolFilter')) document.getElementById('symbolFilter').value = '';
    
    // Clear current filters
    currentFilters.search = '';
    currentFilters.source = '';
    currentFilters.sentiment = '';
    currentFilters.fromDate = '';
    currentFilters.toDate = '';
    currentFilters.symbol = '';
    
    // Reload news
    loadNews(1);
}

/**
 * Refresh news (keep current filters and page)
 */
async function refreshNews() {
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Đang tải...';
    
    try {
        // Reload current page with current filters
        await loadNews(currentPage);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
    }
}

/**
 * Create pagination controls
 */
function createPagination() {
    const container = document.getElementById('paginationContainer');
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginationHTML = '<nav aria-label="News pagination"><ul class="pagination justify-content-center">';
    
    // Previous button
    paginationHTML += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Page numbers
    const maxPages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
    let endPage = Math.min(totalPages, startPage + maxPages - 1);
    
    if (endPage - startPage < maxPages - 1) {
        startPage = Math.max(1, endPage - maxPages + 1);
    }
    
    // First page
    if (startPage > 1) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage(1); return false;">1</a>
            </li>
        `;
        if (startPage > 2) {
            paginationHTML += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }
    
    // Page numbers
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    // Last page
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage(${totalPages}); return false;">${totalPages}</a>
            </li>
        `;
    }
    
    // Next button
    paginationHTML += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginationHTML += '</ul></nav>';
    
    // Add page info
    const startItem = (currentPage - 1) * itemsPerPage + 1;
    const endItem = Math.min(currentPage * itemsPerPage, totalNewsCount);
    paginationHTML += `
        <p class="text-center text-muted mt-2">
            Hiển thị ${startItem}-${endItem} trong tổng số ${totalNewsCount} bài viết
        </p>
    `;
    
    container.innerHTML = paginationHTML;
}

/**
 * Change page
 */
function changePage(page) {
    if (page < 1 || page > totalPages || page === currentPage) return;
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Load new page
    loadNews(page);
}

/**
 * Update statistics
 */
function updateStats() {
    document.getElementById('totalNews').textContent = totalNewsCount;
}

/**
 * Update filter display
 */
function updateFilterDisplay() {
    const activeFilters = [];
    
    if (currentFilters.search) {
        activeFilters.push(`Tìm kiếm: "${currentFilters.search}"`);
    }
    if (currentFilters.source) {
        const sourceName = document.getElementById('sourceFilter').selectedOptions[0].text;
        activeFilters.push(`Nguồn: ${sourceName}`);
    }
    if (currentFilters.sentiment) {
        const sentimentName = document.getElementById('sentimentFilter').selectedOptions[0].text;
        activeFilters.push(`Cảm xúc: ${sentimentName}`);
    }
    if (currentFilters.fromDate || currentFilters.toDate) {
        const fromLabel = currentFilters.fromDate || '...';
        const toLabel = currentFilters.toDate || '...';
        activeFilters.push(`Khoảng ngày: ${fromLabel} → ${toLabel}`);
    }
    if (currentFilters.symbol) {
        activeFilters.push(`Đồng: ${currentFilters.symbol}`);
    }
    
    // Display active filters if any
    const filterDisplay = document.getElementById('activeFiltersDisplay');
    if (filterDisplay) {
        if (activeFilters.length > 0) {
            filterDisplay.innerHTML = `
                <div class="alert alert-info alert-dismissible fade show" role="alert">
                    <i class="fas fa-filter me-2"></i>
                    <strong>Bộ lọc đang áp dụng:</strong> ${activeFilters.join(' • ')}
                    <button type="button" class="btn-close" onclick="clearFilters()"></button>
                </div>
            `;
        } else {
            filterDisplay.innerHTML = '';
        }
    }
}

/**
 * Show error state
 */
function showErrorState(message) {
    const container = document.getElementById('newsContainer');
    container.innerHTML = `
        <div class="col-12">
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-circle me-2"></i>
                ${message}
            </div>
        </div>
    `;
}

/**
 * Auto refresh every 5 minutes
 */
function setupAutoRefresh() {
    setInterval(() => {
        loadNews();
    }, 5 * 60 * 1000);
}

/**
 * Utility: Format date
 */
function formatDate(date) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('vi-VN', options);
}

/**
 * Utility: Format date and time
 */
function formatDateTime(date) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
    };
    return date.toLocaleDateString('vi-VN', options);
}

/**
 * Utility: Get sentiment CSS class
 */
function getSentimentClass(label) {
    if (!label) return 'neutral';
    const lower = label.toLowerCase();
    if (lower.includes('positive') || lower.includes('bullish')) return 'positive';
    if (lower.includes('negative') || lower.includes('bearish')) return 'negative';
    return 'neutral';
}

/**
 * Utility: Get sentiment label in Vietnamese
 */
function getSentimentLabel(label) {
    if (!label) return 'Trung lập';
    const lower = label.toLowerCase();
    if (lower.includes('positive') || lower.includes('bullish')) return 'Tích cực';
    if (lower.includes('negative') || lower.includes('bearish')) return 'Tiêu cực';
    return 'Trung lập';
}

/**
 * Utility: Capitalize source name
 */
function capitalizeSource(source) {
    if (!source) return '';
    return source.split(/(?=[A-Z])/).map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

/**
 * Gửi yêu cầu dừng crawler hiện tại
 */
async function stopCrawl() {
    const button = document.getElementById('crawlStopButton');
    const statusEl = document.getElementById('crawlStatus');
    if (!button) return;

    const originalHtml = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Đang dừng...';

    try {
        const resp = await fetch('/api/admin/crawl/stop', {
            method: 'POST',
        });

        if (!resp.ok) {
            throw new Error('HTTP error ' + resp.status);
        }

        const data = await resp.json();
        if (statusEl) {
            if (data.is_running) {
                statusEl.textContent = 'Đã gửi yêu cầu dừng. Crawler sẽ dừng sau khi hoàn thành nguồn hiện tại.';
            } else {
                statusEl.textContent = 'Hiện không có crawler nào đang chạy.';
            }
        }

        setTimeout(() => {
            if (statusEl) statusEl.textContent = '';
        }, 5000);
    } catch (err) {
        console.error('Error stopping crawl:', err);
        if (statusEl) {
            statusEl.textContent = 'Lỗi khi gửi yêu cầu dừng. Vui lòng thử lại.';
        }
    } finally {
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}

/**
 * Trigger crawlers from UI
 */
async function triggerCrawl() {
    const button = document.getElementById('crawlButton');
    const statusEl = document.getElementById('crawlStatus');
    if (!button) return;

    const originalHtml = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Đang chạy...';
    if (statusEl) {
        statusEl.textContent = 'Đang chạy crawler, vui lòng đợi...';
    }

    try {
        const checkedSources = Array.from(document.querySelectorAll('input[name="crawlSource"]:checked'))
            .map(el => el.value);

        const payload = { sources: checkedSources };

        const resp = await fetch('/api/admin/crawl', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (!resp.ok) {
            throw new Error('HTTP error ' + resp.status);
        }

        await resp.json();

        if (statusEl) {
            statusEl.textContent = 'Crawl hoàn tất. Đang tải lại tin tức...';
        }

        await loadNews(1);

        if (statusEl) {
            setTimeout(() => {
                statusEl.textContent = '';
            }, 5000);
        }
    } catch (err) {
        console.error('Error triggering crawl:', err);
        if (statusEl) {
            statusEl.textContent = 'Lỗi khi chạy crawler. Vui lòng thử lại.';
        }
    } finally {
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}
