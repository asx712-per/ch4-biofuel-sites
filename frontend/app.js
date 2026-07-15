const scanBtn = document.getElementById('scan-btn');
const loader = document.querySelector('.loader');
const btnText = document.querySelector('.btn-text');
const sitesContainer = document.getElementById('sites-container');
const currencySelect = document.getElementById('currency-select');
const globalStats = document.getElementById('global-stats');

const API_BASE = "https://ch4-biofuel-sites.onrender.com"; // Render Production URL

// --- 1. View Navigation (Tabs) ---
const navLinks = document.querySelectorAll('.nav-link');
const views = document.querySelectorAll('.view');

navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Remove active class from all links and views
        navLinks.forEach(l => l.classList.remove('active'));
        views.forEach(v => v.classList.remove('active'));
        
        // Add active class to clicked link and corresponding view
        link.classList.add('active');
        const targetId = link.getAttribute('data-target');
        document.getElementById(targetId).classList.add('active');
        
        // Map requires invalidation if it was hidden during initialization
        if (targetId === 'view-map' && map) {
            setTimeout(() => map.invalidateSize(), 100);
        }
    });
});

// --- 2. Data Fetching & Dashboard ---
async function fetchAndRenderData(currency, minLat = 48.0, maxLat = 54.0, minLon = 6.0, maxLon = 14.0, isMapUpdate = false) {
    if (!isMapUpdate) {
        loader.classList.remove('hidden');
        btnText.textContent = "Scanning...";
        scanBtn.disabled = true;
        sitesContainer.innerHTML = '';
        globalStats.innerHTML = '';
    }

    try {
        const url = `${API_BASE}/api/analyze?currency=${currency}&min_lat=${minLat}&max_lat=${maxLat}&min_lon=${minLon}&max_lon=${maxLon}`;
        const response = await fetch(url);
        
        if (!response.ok) throw new Error("API request failed");
        
        const data = await response.json();
        
        // Always update both views regardless of what triggered the fetch
        renderSites(data.sites);
        updateMapMarkers(data.sites, data.heatmap_url);
        
    } catch (error) {
        console.error(error);
        alert("Scan Failed: " + error.message + "\nMake sure the backend is online.");
        if (!isMapUpdate) {
            sitesContainer.innerHTML = `
                <div class="empty-state" style="border-color: #ef4444; color: #ef4444;">
                    <p>⚠️ Failed to connect to Backend API. Make sure the FastAPI server is running.</p>
                </div>
            `;
        }
    } finally {
        if (!isMapUpdate) {
            loader.classList.add('hidden');
            btnText.textContent = "Run Predictive Scan";
            scanBtn.disabled = false;
        }
    }
}

scanBtn.addEventListener('click', () => {
    const curr = currencySelect.value;
    
    let minLat = 48.0, maxLat = 54.0, minLon = 6.0, maxLon = 14.0;
    
    if (currentDrawnBounds) {
        // User drew a specific rectangle
        minLat = currentDrawnBounds.getSouthWest().lat;
        maxLat = currentDrawnBounds.getNorthEast().lat;
        minLon = currentDrawnBounds.getSouthWest().lng;
        maxLon = currentDrawnBounds.getNorthEast().lng;
    } else if (map) {
        // Fallback to full map viewport
        const bounds = map.getBounds();
        minLat = bounds.getSouthWest().lat;
        maxLat = bounds.getNorthEast().lat;
        minLon = bounds.getSouthWest().lng;
        maxLon = bounds.getNorthEast().lng;
    }
    
    fetchAndRenderData(curr, minLat, maxLat, minLon, maxLon, false);
});

function renderSites(sites) {
    if (!sites || sites.length === 0) {
        sitesContainer.innerHTML = `<div class="empty-state"><p>No viable sites found in this region.</p></div>`;
        return;
    }

    const template = document.getElementById('site-card-template');
    
    let totalProfit = 0;
    let totalCO2e = 0;
    let symbol = "";

    sites.forEach((site, index) => {
        const clone = template.content.cloneNode(true);
        
        // Basic Info
        clone.querySelector('.rank-badge').textContent = `Rank ${index + 1}`;
        clone.querySelector('.site-id').textContent = site.id;
        clone.querySelector('.site-type').textContent = site.type;
        clone.querySelector('.site-location').textContent = `Lat: ${site.latitude.toFixed(4)}, Lon: ${site.longitude.toFixed(4)}`;
        clone.querySelector('.score-value').textContent = Math.round(site.score);

        // Logistics & Finance
        if (site.logistics && site.logistics.feasible) {
            symbol = site.logistics.currency_symbol;
            
            // Logistics Data
            clone.querySelector('.mru-id').textContent = site.logistics.unit_id;
            clone.querySelector('.relocation-dist').textContent = `${site.logistics.relocation_distance_km.toFixed(1)} km`;
            clone.querySelector('.hub-name').textContent = site.logistics.nearest_hub;
            clone.querySelector('.hub-dist').textContent = `${site.logistics.hub_distance_km.toFixed(1)} km`;

            // Finance Data
            const fin = site.finance;
            clone.querySelector('.ethanol-rev').textContent = `${symbol}${fin.revenues.ethanol_sales.toLocaleString()}`;
            clone.querySelector('.carbon-rev').textContent = `${symbol}${fin.revenues.carbon_credits.toLocaleString()}`;
            clone.querySelector('.total-opex').textContent = `${symbol}${fin.expenses.total_expenses.toLocaleString()}`;
            clone.querySelector('.net-profit').textContent = `${symbol}${fin.net_profit.toLocaleString()}`;
            
            clone.querySelector('.roi-value').textContent = `${fin.roi_percentage.toFixed(0)}%`;
            
            // Set ROI bar width (cap at 100%)
            const fillWidth = Math.min(fin.roi_percentage, 100);
            setTimeout(() => {
                const fillElement = sitesContainer.querySelectorAll('.roi-fill')[index];
                if(fillElement) fillElement.style.width = `${fillWidth}%`;
            }, 100);

            totalProfit += fin.net_profit;
            totalCO2e += fin.co2e_avoided_tons;
            
        } else {
            // Unfeasible
            const body = clone.querySelector('.card-body');
            body.innerHTML = `
                <div class="error-state">
                    <strong>Logistics Unfeasible:</strong> ${site.logistics ? site.logistics.reason : "Unknown error"}
                </div>
            `;
            clone.querySelector('.card-footer').style.display = 'none';
        }

        sitesContainer.appendChild(clone);
    });

    // Update Global Stats
    if (totalProfit > 0) {
        globalStats.innerHTML = `
            <div style="text-align: right;">
                <p style="font-size: 0.85rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Total Network Profit</p>
                <p style="font-size: 1.5rem; color: #064e3b; font-weight: 700;">${symbol}${totalProfit.toLocaleString()}</p>
                <p style="font-size: 0.85rem; color: #10b981; font-weight: 600;">+${totalCO2e.toLocaleString()}t CO2e Offset</p>
            </div>
        `;
    }
}


// --- 3. Live Interactive Leaflet Map ---
let map;
let markerLayer = L.layerGroup();
let drawnItems = new L.FeatureGroup();
let currentDrawnBounds = null;

function initMap() {
    // Default focus on Germany/Europe
    map = L.map('leaflet-map').setView([51.0, 10.0], 5);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    map.addLayer(drawnItems);
    markerLayer.addTo(map);

    // Initialize Leaflet Draw Control
    const drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems,
            remove: true
        },
        draw: {
            polygon: false,
            polyline: false,
            circle: false,
            circlemarker: false,
            marker: false,
            rectangle: {
                shapeOptions: {
                    color: '#064e3b',
                    weight: 2,
                    fillOpacity: 0.1
                }
            }
        }
    });
    map.addControl(drawControl);

    // Handle Draw Events
    map.on(L.Draw.Event.CREATED, function (e) {
        drawnItems.clearLayers(); // Only allow one selection box at a time
        const layer = e.layer;
        drawnItems.addLayer(layer);
        
        currentDrawnBounds = layer.getBounds();
    });
    
    map.on(L.Draw.Event.DELETED, function (e) {
        if (drawnItems.getLayers().length === 0) {
            currentDrawnBounds = null;
        }
    });

    // Auto-scanning on pan has been disabled to give user control via selection.
}

let currentHeatmapLayer = null;

function updateMapMarkers(sites, heatmapUrl = null) {
    markerLayer.clearLayers();
    
    // 1. Handle Heatmap Overlay
    if (currentHeatmapLayer) {
        map.removeLayer(currentHeatmapLayer);
        currentHeatmapLayer = null;
    }
    
    if (heatmapUrl) {
        currentHeatmapLayer = L.tileLayer(heatmapUrl, {
            opacity: 0.6,
            zIndex: 10,
            maxNativeZoom: 12 // Prevents EE from failing at high zoom levels
        }).addTo(map);
    }
    
    // 2. Handle Site Markers
    if (!sites) return;

    sites.forEach(site => {
        const isFeasible = site.logistics && site.logistics.feasible;
        
        // Create custom dot marker based on feasibility
        const color = isFeasible ? '#10b981' : '#ef4444';
        
        const circleMarker = L.circleMarker([site.latitude, site.longitude], {
            radius: 8,
            fillColor: color,
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        });

        let popupContent = `
            <div style="font-family: 'Inter', sans-serif;">
                <h3>${site.id}</h3>
                <p>${site.type}</p>
                <p><strong>Feasibility Score:</strong> ${Math.round(site.score)}/100</p>
        `;

        if (isFeasible) {
            const sym = site.logistics.currency_symbol;
            popupContent += `
                <p><strong>Offtake Route:</strong> ${site.logistics.hub_distance_km.toFixed(1)}km to ${site.logistics.nearest_hub}</p>
                <span class="roi">ROI: ${site.finance.roi_percentage.toFixed(0)}%</span>
            `;
        } else {
            popupContent += `
                <p style="color: #ef4444; margin-top: 10px;"><strong>Status:</strong> ${site.logistics.reason}</p>
            `;
        }

        popupContent += `</div>`;
        
        circleMarker.bindPopup(popupContent);
        markerLayer.addLayer(circleMarker);
    });
}

// Initialize Map immediately
initMap();
