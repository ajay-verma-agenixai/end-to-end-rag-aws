function showLoading() {
    document.getElementById('loadingSpinner').classList.remove('d-none');
    document.getElementById('results').innerHTML = '';
}

function hideLoading() {
    document.getElementById('loadingSpinner').classList.add('d-none');
}

function setFilter(filterType) {
    const searchInput = document.getElementById('searchInput');
    const filters = {
        'elderly': 'Find comprehensive health checkup packages for elderly people',
        'children': 'Find health checkup packages suitable for children',
        'women': 'Find women\'s health checkup packages',
        'basic': 'Find basic health checkup packages',
        'comprehensive': 'Find comprehensive health checkup packages'
    };
    searchInput.value = filters[filterType];
    searchPackages();
}

function displayError(message) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <h4 class="alert-heading">Error!</h4>
            <p>${message}</p>
            <hr>
            <p class="mb-0">Please try again or contact support if the problem persists.</p>
        </div>
    `;
}

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';

    if (data.error) {
        displayError(data.error);
        return;
    }

    if (!data.packages || data.packages.length === 0) {
        resultsDiv.innerHTML = `
            <div class="alert alert-info" role="alert">
                <h4 class="alert-heading">No Packages Found</h4>
                <p>No health packages found matching your criteria. Please try:</p>
                <ul>
                    <li>Using different keywords</li>
                    <li>Broadening your search criteria</li>
                    <li>Checking the spelling of hospital names</li>
                </ul>
            </div>
        `;
        return;
    }

    data.packages.forEach(package => {
        const packageCard = document.createElement('div');
        packageCard.className = 'package-card';
        packageCard.innerHTML = `
            <div class="package-header">
                <h4>${package.hospital}</h4>
                <div class="package-price">₹${package.price}</div>
            </div>
            <div class="package-details">
                <p>${package.description}</p>
            </div>
            <div class="package-features">
                <h5>Package Includes:</h5>
                <ul>
                    ${package.features.map(feature => `
                        <li class="feature-item">
                            <i class="fas fa-check-circle"></i>
                            ${feature}
                        </li>
                    `).join('')}
                </ul>
            </div>
            <div class="mt-3">
                <a href="${package.booking_link || '#'}" class="btn btn-primary" target="_blank">Book Now</a>
            </div>
        `;
        resultsDiv.appendChild(packageCard);
    });
}

async function searchPackages() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();

    if (!query) {
        displayError('Please enter a search query');
        return;
    }

    showLoading();

    try {
        console.log('Sending query:', query);
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });

        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to get response from API');
        }
        
        displayResults(data);
    } catch (error) {
        console.error('Search error:', error);
        displayError(error.message || 'Failed to fetch results. Please try again.');
    } finally {
        hideLoading();
    }
}

// Add event listener for Enter key
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        searchPackages();
    }
}); 