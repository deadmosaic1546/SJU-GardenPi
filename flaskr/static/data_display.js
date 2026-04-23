// Plot comes from flaskr
function getPlotIdFromURL() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
}

const plot_id = getPlotIdFromURL();

function renderData(data) {
    const container = document.getElementById("bottom");
    container.innerHTML = ''; // clear previous content
    if (data.error) {
        container.innerHTML = `<p>${data.error}</p>`;
        return;
    }
    const card = document.createElement('div');
    card.id = 'switch';
    card.innerHTML = `
            <h1 id="dominant">Pico ${data.plot_id} Last Updated: ${data.time}</h1>
            <h2>Light Level: ${data.light}</h2>
            <h2>Humidity: ${data.humidity}</h2>
            <h2>Soil Moisture: ${data.moisture}</h2>
            <h2>Air Temperature: ${data.air_temp}</h2>
            <h2>Soil Temperature: ${data.soil_temp}</h2>
        `;
    container.appendChild(card);
}

async function fetchPlot(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (!response.ok) {
            const errInfo = await response.json().catch(() => ({}));
            let message = `HTTP error ${response.status}`;
            if (errInfo.error) message += `: ${errInfo.error}`;
            return { error: message };
        }
        return await response.json();
    } catch (err) {
        console.error(err);
        return { error: 'Failed to load plot data.' };
    }
}

async function loadData() {
    const data = await fetchPlot(`/api/pull/${plot_id}`);
    if (data) renderData(data);
}

async function loadLive() {
    const data = await fetchPlot(`/api/live/${plot_id}`);
    if (data) renderData(data);
}

async function loadDailyAverage() {
    const data = await fetchPlot(`/api/average/daily/${plot_id}`);
    if (data) renderData(data);
}

async function loadWeeklyAverage() {
    const data = await fetchPlot(`/api/average/weekly/${plot_id}`);
    if (data) renderData(data);
}

async function loadMonthlyAverage() {
    const data = await fetchPlot(`/api/average/monthly/${plot_id}`);
    if (data) renderData(data);
}

async function loadBeds() {
    for (let bedId = 1; bedId <= 4; bedId++) {
        const data = await fetchPlot(`/api/pull/${bedId}`);
        const bedDiv = document.getElementById(`bed${bedId}`);
        if (data.error) {
            bedDiv.innerHTML = `<h1>Bed ${bedId}</h1><h2>Unable to load data for ${bedId}</h2>`;
        } else {
            bedDiv.innerHTML = `
                <h1>Bed ${bedId}</h1>
                <h2>Light Level: ${data.light ? data.light.toFixed(2) : 'N/A'}</h2>
                <h2>Air Temperature: ${data.air_temp ? data.air_temp.toFixed(2) : 'N/A'}°F</h2>
                <h2>Humidity: ${data.humidity ? data.humidity.toFixed(2) : 'N/A'}%</h2>
                <h2>Soil Moisture: ${data.moisture ? data.moisture.toFixed(2) : 'N/A'}</h2>
                <h2>Soil Temperature: ${data.soil_temp ? data.soil_temp.toFixed(2) : 'N/A'}°F</h2>
            `;
        }
    }
}

// initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname === '/') {
        loadBeds();
    } else {
        loadData();
        document.getElementById('mostRecentBtn').addEventListener('click', loadData);
        document.getElementById('liveBtn').addEventListener('click', loadLive);
        document.getElementById('dailyBtn').addEventListener('click', loadDailyAverage);
        document.getElementById('weeklyBtn').addEventListener('click', loadWeeklyAverage);
        document.getElementById('monthlyBtn').addEventListener('click', loadMonthlyAverage);
    }
});