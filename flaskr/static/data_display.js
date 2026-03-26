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
        const container = document.getElementById("bottom");
        if (!response.ok) {
            const errInfo = await response.json().catch(() => ({}));
            let message = `HTTP error ${response.status}`;
            if (errInfo.error) message += `: ${errInfo.error}`;
            container.innerHTML = `<p>${message}</p>`;
            return null;
        }
        return await response.json();
    } catch (err) {
        console.error(err);
        const container = document.getElementById("bottom");
        container.innerHTML = '<p>Failed to load plot data.</p>';
        return null;
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



// initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    document.getElementById('liveBtn').addEventListener('click', loadLive);
});