const scanBtn = document.getElementById('scan-btn');
const loader = document.querySelector('.loader');
const btnText = document.querySelector('.btn-text');
const sitesContainer = document.getElementById('sites-container');
const currencySelect = document.getElementById('currency-select');
const globalStats = document.getElementById('global-stats');

const API_BASE = "https://ch4-biofuel-sites.onrender.com"; // Render Production URL

scanBtn.addEventListener('click', async () => {
    // UI Loading State
    loader.classList.remove('hidden');
    btnText.textContent = "Scanning...";
    scanBtn.disabled = true;
    sitesContainer.innerHTML = '';
    globalStats.innerHTML = '';

    try {
        const currency = currencySelect.value;
        const response = await fetch(`${API_BASE}/api/analyze?currency=${currency}`);
        
        if (!response.ok) throw new Error("API request failed");
        
        const data = await response.json();
        renderSites(data.sites);
        
    } catch (error) {
        console.error(error);
        sitesContainer.innerHTML = `
            <div class="empty-state" style="border-color: #ef4444; color: #ef4444;">
                <p>⚠️ Failed to connect to Backend API. Make sure the FastAPI server is running.</p>
            </div>
        `;
    } finally {
        // Reset UI
        loader.classList.add('hidden');
        btnText.textContent = "Run Predictive Scan";
        scanBtn.disabled = false;
    }
});

function renderSites(sites) {
    if (!sites || sites.length === 0) {
        sitesContainer.innerHTML = `<div class="empty-state"><p>No viable sites found.</p></div>`;
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
