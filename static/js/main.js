document.addEventListener('DOMContentLoaded', () => {
    // === UPLOAD PAGE LOGIC ===
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('uploadForm');
    
    if (uploadArea && fileInput) {
        const browseBtn = document.getElementById('browseBtn');
        const imagePreview = document.getElementById('imagePreview');
        const uploadPrompt = document.getElementById('uploadPrompt');
        const previewImg = imagePreview.querySelector('img');
        const removeBtn = document.getElementById('removeBtn');
        const loadingOverlay = document.getElementById('loadingOverlay');
        const resultCard = document.getElementById('resultCard');
        const latInput = document.getElementById('latInput');
        const lngInput = document.getElementById('lngInput');

        // Get Location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    latInput.value = position.coords.latitude;
                    lngInput.value = position.coords.longitude;
                },
                (error) => console.log('Geolocation error:', error)
            );
        }

        browseBtn.addEventListener('click', () => fileInput.click());

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFileSelect();
            }
        });

        fileInput.addEventListener('change', handleFileSelect);

        removeBtn.addEventListener('click', () => {
            fileInput.value = '';
            imagePreview.classList.add('d-none');
            uploadPrompt.classList.remove('d-none');
            resultCard.classList.add('d-none');
        });

        function handleFileSelect() {
            if (fileInput.files && fileInput.files[0]) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    previewImg.src = e.target.result;
                    uploadPrompt.classList.add('d-none');
                    imagePreview.classList.remove('d-none');
                }
                reader.readAsDataURL(fileInput.files[0]);
            }
        }

        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!fileInput.files.length) return;

            uploadArea.classList.add('d-none');
            loadingOverlay.classList.remove('d-none');
            resultCard.classList.add('d-none');

            const formData = new FormData(uploadForm);

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                loadingOverlay.classList.add('d-none');
                
                if (data.error) {
                    alert('Error: ' + data.error);
                    uploadArea.classList.remove('d-none');
                    return;
                }

                // Build result card
                const severityColor = data.severity === 'SEVERE' ? 'danger' : (data.severity === 'MODERATE' ? 'warning' : 'info');
                
                resultCard.innerHTML = `
                    <div class="glass-card p-4 rounded-4 shadow-lg border border-${severityColor} border-opacity-50 text-start">
                        <div class="row align-items-center mb-4">
                            <div class="col-md-8">
                                <h3 class="font-outfit fw-bold text-light mb-1">Analysis Complete</h3>
                                <p class="text-light opacity-75 mb-0">Found ${data.total_detected} potential hazard(s).</p>
                            </div>
                            <div class="col-md-4 text-md-end mt-3 mt-md-0">
                                <span class="badge bg-${severityColor} fs-5 px-4 py-2 rounded-pill">${data.severity}</span>
                            </div>
                        </div>
                        
                        <div class="row g-4">
                            <div class="col-md-6">
                                <img src="${data.processed_image}" class="img-fluid rounded-3 border border-light border-opacity-10 shadow" alt="Processed">
                            </div>
                            <div class="col-md-6">
                                <div class="glass-card p-3 rounded-3 mb-3">
                                    <h6 class="text-light opacity-50 small mb-1">Recommended Action</h6>
                                    <h5 class="text-light fw-medium mb-0">${data.recommendation}</h5>
                                </div>
                                <div class="glass-card p-3 rounded-3 mb-3">
                                    <h6 class="text-light opacity-50 small mb-1">Risk Assessment</h6>
                                    <h5 class="text-light fw-medium mb-0">${data.risk}</h5>
                                </div>
                                <div class="d-grid gap-2">
                                    <a href="/dashboard" class="btn btn-primary rounded-pill fw-medium">View Full Dashboard</a>
                                    <button class="btn btn-outline-light rounded-pill" onclick="location.reload()">Report Another</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                resultCard.classList.remove('d-none');
                
            } catch (error) {
                console.error(error);
                alert('An error occurred during analysis.');
                loadingOverlay.classList.add('d-none');
                uploadArea.classList.remove('d-none');
            }
        });
    }

    // === MAP & ANALYTICS PAGE LOGIC ===
    const mapElement = document.getElementById('map');
    if (mapElement) {
        // Initialize Map
        const map = L.map('map').setView([0, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        let markersLayer = L.layerGroup().addTo(map);
        let heatLayer = null;

        // Fetch data
        Promise.all([
            fetch('/api/history').then(r => r.json()),
            fetch('/api/heatmap-data').then(r => r.json())
        ]).then(([history, heatData]) => {
            
            // Stats for chart
            let severe = 0, mod = 0, minor = 0;
            const recentList = document.getElementById('recentReportsList');
            
            history.forEach((item, index) => {
                if (item.severity === 'SEVERE') severe++;
                else if (item.severity === 'MODERATE') mod++;
                else minor++;
                
                // Add Marker if has coords
                if (item.latitude && item.longitude) {
                    let color = item.severity === 'SEVERE' ? 'red' : (item.severity === 'MODERATE' ? 'orange' : 'blue');
                    
                    const markerHtml = `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.5);"></div>`;
                    const icon = L.divIcon({ html: markerHtml, className: 'custom-leaflet-marker' });
                    
                    L.marker([item.latitude, item.longitude], {icon: icon})
                        .bindPopup(`<b>Report #${item.id}</b><br>Severity: ${item.severity}<br><a href="/api/results/${item.id}" target="_blank">View JSON Data</a>`)
                        .addTo(markersLayer);
                        
                    // Center map on latest point
                    if (index === 0) map.setView([item.latitude, item.longitude], 12);
                }
                
                // Populate recent list
                if (index < 5 && recentList) {
                    let badgeClass = item.severity === 'SEVERE' ? 'danger' : (item.severity === 'MODERATE' ? 'warning' : 'info');
                    recentList.innerHTML += `
                        <div class="d-flex justify-content-between align-items-center border-bottom border-light border-opacity-10 py-2">
                            <span class="text-light opacity-75 small font-inter">#${item.id} - ${item.timestamp.split('T')[0]}</span>
                            <span class="badge bg-${badgeClass}">${item.severity}</span>
                        </div>
                    `;
                }
            });

            // Add Heatmap
            if (heatData.length > 0) {
                heatLayer = L.heatLayer(heatData, {radius: 25, blur: 15, maxZoom: 17}).addTo(map);
            }
            
            // Chart.js
            const ctx = document.getElementById('severityChart');
            if (ctx) {
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Severe', 'Moderate', 'Minor'],
                        datasets: [{
                            data: [severe, mod, minor],
                            backgroundColor: ['#EF4444', '#F59E0B', '#3B82F6'],
                            borderWidth: 0,
                            hoverOffset: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { color: '#F8FAFC' }
                            }
                        }
                    }
                });
            }
        });

        // Toggles
        document.getElementById('toggleHeatmap')?.addEventListener('change', (e) => {
            if(heatLayer) { e.target.checked ? map.addLayer(heatLayer) : map.removeLayer(heatLayer); }
        });
        
        document.getElementById('toggleMarkers')?.addEventListener('change', (e) => {
            e.target.checked ? map.addLayer(markersLayer) : map.removeLayer(markersLayer);
        });
    }

    // === THEME TOGGLE LOGIC ===
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const body = document.body;
            const icon = themeToggle.querySelector('i');
            if (body.classList.contains('dark-theme')) {
                body.classList.remove('dark-theme');
                body.classList.add('light-theme');
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
                document.documentElement.style.setProperty('--dark-bg', '#F8FAFC');
                document.documentElement.style.setProperty('--darker-bg', '#E2E8F0');
                document.documentElement.style.setProperty('--glass-bg', 'rgba(255, 255, 255, 0.7)');
                document.documentElement.style.setProperty('--glass-border', 'rgba(0, 0, 0, 0.1)');
                body.style.color = '#0F172A';
                document.querySelectorAll('.text-light').forEach(el => {
                    el.classList.remove('text-light');
                    el.classList.add('text-dark');
                });
            } else {
                body.classList.remove('light-theme');
                body.classList.add('dark-theme');
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
                document.documentElement.style.setProperty('--dark-bg', '#0B0F19');
                document.documentElement.style.setProperty('--darker-bg', '#05080F');
                document.documentElement.style.setProperty('--glass-bg', 'rgba(15, 23, 42, 0.6)');
                document.documentElement.style.setProperty('--glass-border', 'rgba(255, 255, 255, 0.08)');
                body.style.color = '#F8FAFC';
                document.querySelectorAll('.text-dark').forEach(el => {
                    el.classList.remove('text-dark');
                    el.classList.add('text-light');
                });
            }
        });
    }
});
