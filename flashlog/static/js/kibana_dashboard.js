// FlashLog Dashboard JS

document.addEventListener('DOMContentLoaded', function() {
    // Chart.js Pie for Anomaly vs Total Logs
    const anomalyTotalChart = new Chart(document.getElementById('anomalyTotalChart').getContext('2d'), {
        type: 'pie',
        data: {
            labels: ['Normal Logs', 'Anomalies'],
            datasets: [{
                data: [1800, 200], // Placeholder, replace with AJAX
                backgroundColor: ['#34d399', '#f87171'],
            }]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            let value = context.parsed;
                            let total = context.chart._metasets[0].total;
                            let percent = ((value / total) * 100).toFixed(2);
                            return `${label}: ${value} (${percent}%)`;
                        }
                    }
                }
            }
        }
    });

    // Chart.js Bar for Anomaly Types
    const anomalyTypeChart = new Chart(document.getElementById('anomalyTypeChart').getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Broken Access Control', 'Brute Force', 'Privilege Escalation', 'Log Injection'],
            datasets: [{
                label: 'Occurrences',
                data: [200, 120, 90, 90], // Placeholder, replace with AJAX
                backgroundColor: ['#6366f1', '#f59e42', '#10b981', '#f43f5e'],
            }]
        },
        options: {
            responsive: true,
            onClick: function(evt, elements) {
                if (elements.length > 0) {
                    const idx = elements[0].index;
                    const type = this.data.labels[idx];
                    loadAnomalyTypeLogs(type);
                }
            }
        }
    });

    // Load anomaly type list
    function loadAnomalyTypeList() {
        // Placeholder: Replace with AJAX
        const types = [
            { type: 'Broken Access Control', count: 200, icon: '🔓' },
            { type: 'Brute Force', count: 120, icon: '🔐' },
            { type: 'Privilege Escalation', count: 90, icon: '🧬' },
            { type: 'Log Injection', count: 90, icon: '🧾' }
        ];
        const container = document.getElementById('anomalyTypeList');
        container.innerHTML = '';
        types.forEach(t => {
            const btn = document.createElement('button');
            btn.className = 'px-3 py-1 rounded bg-blue-100 text-blue-800 font-semibold mr-2 mb-2 hover:bg-blue-200';
            btn.innerHTML = `${t.icon} ${t.type} <span class="ml-1 text-xs bg-blue-200 rounded px-2">${t.count}</span>`;
            btn.onclick = () => loadAnomalyTypeLogs(t.type);
            container.appendChild(btn);
        });
    }

    // Load logs for a given anomaly type
    function loadAnomalyTypeLogs(type) {
        // Placeholder: Replace with AJAX
        const logs = [
            { id: 1, content: 'User admin failed login 5 times', timestamp: '2025-07-21 18:45:35', source: '192.168.1.1', reason: 'Brute Force', score: 0.98 },
            { id: 2, content: 'Suspicious privilege escalation detected', timestamp: '2025-07-21 18:46:10', source: '192.168.1.2', reason: 'Privilege Escalation', score: 0.92 }
        ];
        const details = document.getElementById('logDetails');
        details.innerHTML = logs.map(log => `
            <div class="border-b py-2 cursor-pointer hover:bg-gray-50" onclick="showLogDetail(${log.id})">
                <div class="font-mono text-sm">${log.content}</div>
                <div class="text-xs text-gray-500">${log.timestamp} | Source: ${log.source} | Score: ${log.score}</div>
            </div>
        `).join('');
        // Show mitigation for the first log (placeholder)
        showMitigation(type);
    }

    // Show log detail (expandable)
    window.showLogDetail = function(logId) {
        // Placeholder: Replace with AJAX
        const log = { id: logId, content: 'User admin failed login 5 times', timestamp: '2025-07-21 18:45:35', source: '192.168.1.1', reason: 'Brute Force', score: 0.98 };
        const details = document.getElementById('logDetails');
        details.innerHTML = `
            <div class="p-4 bg-gray-100 rounded">
                <div class="font-mono text-base mb-2">${log.content}</div>
                <div class="text-xs text-gray-500 mb-1">Timestamp: ${log.timestamp}</div>
                <div class="text-xs text-gray-500 mb-1">Source: ${log.source}</div>
                <div class="text-xs text-gray-500 mb-1">Reason: ${log.reason}</div>
                <div class="text-xs text-gray-500 mb-1">Score: ${log.score}</div>
            </div>
        `;
        showMitigation(log.reason);
    }

    // Show mitigation guidance
    function showMitigation(type) {
        const guidance = {
            'Broken Access Control': 'Ensure role-based access checks are implemented correctly at both frontend and backend.',
            'Brute Force': 'Implement account lockout and rate limiting for failed login attempts.',
            'Privilege Escalation': 'Review user permissions and audit privilege changes.',
            'Log Injection': 'Sanitize all log inputs and validate log formats.'
        };
        document.getElementById('mitigationGuidance').innerText = guidance[type] || 'No guidance available.';
    }

    // Export buttons
    document.getElementById('exportCSV').onclick = function() {
        alert('Export CSV (to be implemented)');
    };
    document.getElementById('exportPDF').onclick = function() {
        alert('Export PDF (to be implemented)');
    };

    // Search
    document.getElementById('searchInput').oninput = function(e) {
        // Placeholder: Implement search/filter logic
        alert('Search/filter (to be implemented)');
    };

    // Initial load
    loadAnomalyTypeList();
}); 