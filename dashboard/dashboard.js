const host = 'aw-project3855-w2025.eastus2.cloudapp.azure.com';

const statsUrl = `http://${host}:8110/stats`;
const analyzerUrl = `http://${host}:8100/analyzer`;
const randomEventUrl = `http://${host}:8100/random-event`;


// Function to fetch and update statistics
async function fetchStats() {
    const response = await fetch(statsUrl);
    const data = await response.json();
    document.getElementById('stats').textContent = JSON.stringify(data, null, 2);
    document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
}

// Function to fetch and update analyzer data
async function fetchAnalyzerData() {
    const response = await fetch(analyzerUrl);
    const data = await response.json();
    document.getElementById('analyzer').textContent = JSON.stringify(data, null, 2);
}

// Function to fetch and display a random event
async function fetchRandomEvent() {
    const response = await fetch(randomEventUrl);
    const data = await response.json();
    document.getElementById('random-event').textContent = JSON.stringify(data, null, 2);
}

// Update the data every 2–4 seconds
setInterval(() => {
    fetchStats();
    fetchAnalyzerData();
    fetchRandomEvent();
}, Math.random() * 2000 + 2000);  // Random interval between 2 and 4 seconds
