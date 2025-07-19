document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        const tableRows = document.querySelectorAll('#itemTable tr');
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            tableRows.forEach(row => {
                const name = row.cells[1].textContent.toLowerCase();
                row.style.display = name.includes(searchTerm) ? '' : 'none';
            });
        });
    } else {
        console.warn('Search input element not found');
    }

    // Chart.js Integration with Error Handling
    const ctx = document.getElementById('stockChart');
    if (ctx && ctx.getContext) {
        const canvasCtx = ctx.getContext('2d');
        const totalItems = parseInt('{{ items|length }}') || 0;
        const lowStock = parseInt('{{ low_stock_count }}') || 0;
        const expiring = parseInt('{{ expiring_count }}') || 0;

        new Chart(canvasCtx, {
            type: 'bar',
            data: {
                labels: ['Total Items', 'Low Stock', 'Expiring'],
                datasets: [{
                    label: 'Inventory Status',
                    data: [totalItems, lowStock, expiring],
                    backgroundColor: ['#4CAF50', '#FF6384', '#FFCE56']
                }]
            },
            options: {
                scales: { y: { beginAtZero: true } },
                plugins: {
                    legend: { position: 'top' }
                }
            }
        });
    } else {
        console.error('Canvas element or context not found for Chart.js');
    }
});