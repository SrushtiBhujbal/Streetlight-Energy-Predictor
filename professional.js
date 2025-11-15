// Enhanced Professional Streetlight Energy Optimizer JavaScript
class StreetlightPredictor {
    constructor() {
        this.apiBase = '';
        this.currentPrediction = null;
        this.savingsChart = null;
        this.initializeEventListeners();
        this.loadModelInfo();
        this.initializeCharts();
    }

    initializeEventListeners() {
        // Form submission
        document.getElementById('predictionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handlePrediction();
        });

        // Real-time updates for range inputs
        this.initializeRangeInputs();
        
        // Initialize descriptions
        this.updateTimeBasedFields();
        this.updateWeatherDescription();
    }

    initializeRangeInputs() {
        // Set initial values
        this.updateHourValue(14);
        this.updateCloudValue(20);
        this.updatePrecipValue(0);
        this.updateHumidityValue(50);
        this.updateVisibilityValue(10);
        this.updateWindValue(10);
        this.updateTempValue(25);
    }

    updateHourValue(value) {
        document.getElementById('hour').value = value;
        document.getElementById('hourValue').textContent = `${value}:00`;
        this.updateTimeBasedFields();
    }

    updateCloudValue(value) {
        document.getElementById('cloud').value = value;
        document.getElementById('cloudValue').textContent = `${value}%`;
        this.updateWeatherDescription();
    }

    updatePrecipValue(value) {
        document.getElementById('precipitation_mm').value = value;
        document.getElementById('precipValue').textContent = `${value} mm`;
    }

    updateHumidityValue(value) {
        document.getElementById('humidity').value = value;
        document.getElementById('humidityValue').textContent = `${value}%`;
    }

    updateVisibilityValue(value) {
        document.getElementById('visibility_km').value = value;
        document.getElementById('visibilityValue').textContent = `${value} km`;
    }

    updateWindValue(value) {
        document.getElementById('wind_speed_kph').value = value;
        document.getElementById('windValue').textContent = `${value} kph`;
    }

    updateTempValue(value) {
        document.getElementById('temperature_final').value = value;
        document.getElementById('tempValue').textContent = `${value}°C`;
    }

    updateTimeBasedFields() {
        const hour = parseInt(document.getElementById('hour').value) || 12;
        const isNight = hour >= 19 || hour <= 6;
        
        // Update visual indicator
        const timeIndicator = document.getElementById('timeIndicator');
        if (timeIndicator) {
            timeIndicator.textContent = isNight ? '🌙 Night Time' : '☀️ Day Time';
            timeIndicator.className = `time-indicator ${isNight ? 'night' : 'day'}`;
        }
    }

    updateWeatherDescription() {
        const cloud = parseInt(document.getElementById('cloud').value) || 0;
        
        let description = '';
        if (cloud < 20) description = '☀️ Clear Sky';
        else if (cloud < 50) description = '🌤️ Partly Cloudy';
        else if (cloud < 80) description = '☁️ Cloudy';
        else description = '🌫️ Overcast';
        
        const weatherIndicator = document.getElementById('weatherIndicator');
        if (weatherIndicator) {
            weatherIndicator.textContent = description;
        }
    }

    async loadModelInfo() {
        try {
            const response = await fetch('/api/model-info');
            const info = await response.json();
            this.displayModelInfo(info);
        } catch (error) {
            console.error('Failed to load model info:', error);
        }
    }

    displayModelInfo(info) {
        // Info is displayed in the hero badge via Jinja2 template
    }

    async handlePrediction() {
        this.showLoading(true);
        
        try {
            const formData = this.collectFormData();
            const prediction = await this.makePrediction(formData);
            this.displayPrediction(prediction);
            this.updateAnalytics(prediction);
        } catch (error) {
            this.displayError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    collectFormData() {
        const form = document.getElementById('predictionForm');
        const formData = new FormData(form);
        const data = {};
        
        // Collect all form values
        for (let [key, value] of formData.entries()) {
            data[key] = parseFloat(value) || 0;
        }
        
        // Add computed fields
        const hour = data.hour || 12;
        data.is_night = (hour >= 19 || hour <= 6) ? 1 : 0;
        
        // Set default values for required fields
        const defaults = {
            power_consumption_watts: 150,
            voltage_volts: 220,
            current_amperes: 0.68,
            wind_speed_kph: data.wind_speed_kph || 10,
            day_length_minutes: 840,
            weather_severity: Math.min(30, (data.cloud || 0) * 0.3 + (data.precipitation_mm || 0) * 5),
            is_clear_sky: (data.cloud || 0) < 20 ? 1 : 0,
            natural_light_score: Math.max(0, 1 - ((data.cloud || 0) / 100)),
            weather_energy_factor: 1.0 + ((data.cloud || 0) / 100) * 0.1
        };
        
        return { ...defaults, ...data };
    }

    async makePrediction(data) {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Prediction failed');
        }
        
        return result;
    }

    displayPrediction(prediction) {
        this.currentPrediction = prediction;
        const resultCard = document.getElementById('resultCard');
        const defaultResult = document.getElementById('defaultResult');
        
        // Hide default result, show prediction result
        defaultResult.style.display = 'none';
        resultCard.style.display = 'block';
        
        // Build the result HTML
        const isOn = prediction.status === 'ON';
        const statusColor = isOn ? 'status-on' : 'status-off';
        const statusIcon = isOn ? '💡' : '⚡';
        const statusText = isOn ? 'TURN LIGHTS ON' : 'TURN LIGHTS OFF';
        const cardClass = isOn ? 'recommend-on' : 'recommend-off';
        
        // Build condition details HTML
        const conditionDetails = prediction.details.map(detail => `
            <div class="condition-item">
                <div class="condition-icon">${detail.icon}</div>
                <div class="condition-text">${detail.text}</div>
            </div>
        `).join('');
        
        resultCard.innerHTML = `
            <div class="status-header">
                <div class="status-indicator ${statusColor}">${statusIcon}</div>
                <div class="status-text">${statusText}</div>
            </div>
            
            <div class="confidence-meter">
                <div class="confidence-value">${(prediction.confidence * 100).toFixed(1)}%</div>
                <div class="confidence-label">AI Confidence Level</div>
            </div>
            
            <div class="explanation-box">
                ${prediction.explanation}
            </div>
            
            <div class="condition-details">
                ${conditionDetails}
            </div>
            
            <div class="energy-impact">
                <h4>💰 Immediate Impact</h4>
                <p>This recommendation could save <strong>${prediction.energy_savings.hourly}W per hour</strong> while maintaining safety standards.</p>
            </div>
        `;
        
        resultCard.className = `result-card ${cardClass} fade-in`;
        
        // Show analytics section
        document.getElementById('analyticsSection').style.display = 'block';
        
        // Scroll to results
        setTimeout(() => {
            resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 300);
    }

    updateAnalytics(prediction) {
        // Update analytics cards
        document.getElementById('hourlySavings').textContent = `${prediction.energy_savings.hourly}W`;
        document.getElementById('dailySavings').textContent = `${this.formatNumber(prediction.energy_savings.daily)}W`;
        document.getElementById('monthlySavings').textContent = `${this.formatNumber(prediction.energy_savings.monthly)}W`;
        document.getElementById('co2Savings').textContent = `${prediction.energy_savings.co2}kg`;
        
        // Update chart
        this.updateSavingsChart(prediction);
    }

    initializeCharts() {
        const ctx = document.getElementById('savingsChart').getContext('2d');
        this.savingsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Hourly', 'Daily', 'Monthly'],
                datasets: [{
                    label: 'Energy Savings (W)',
                    data: [0, 0, 0],
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(118, 75, 162, 0.8)',
                        'rgba(39, 174, 96, 0.8)'
                    ],
                    borderColor: [
                        'rgb(102, 126, 234)',
                        'rgb(118, 75, 162)',
                        'rgb(39, 174, 96)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Potential Energy Savings'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Watts Saved'
                        }
                    }
                }
            }
        });
    }

    updateSavingsChart(prediction) {
        if (this.savingsChart) {
            this.savingsChart.data.datasets[0].data = [
                prediction.energy_savings.hourly,
                prediction.energy_savings.daily / 1000, // Scale down for chart
                prediction.energy_savings.monthly / 10000 // Scale down for chart
            ];
            this.savingsChart.update();
        }
    }

    displayError(message) {
        const resultCard = document.getElementById('resultCard');
        resultCard.innerHTML = `
            <div class="text-center">
                <div style="font-size: 3em; margin: 20px 0;">❌</div>
                <div style="color: var(--danger); font-size: 1.2em; margin: 10px 0;">
                    Prediction Failed
                </div>
                <div style="color: var(--gray);">
                    ${message}
                </div>
            </div>
        `;
        resultCard.style.display = 'block';
        resultCard.className = 'result-card';
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        const button = document.querySelector('.btn-primary');
        
        if (show) {
            overlay.style.display = 'flex';
            button.classList.add('loading');
            button.innerHTML = '<span class="btn-icon">⏳</span> Analyzing...';
        } else {
            overlay.style.display = 'none';
            button.classList.remove('loading');
            button.innerHTML = '<span class="btn-icon">🤖</span> Get AI Recommendation';
        }
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
}

// Scenario loader
function loadScenario(type) {
    const scenarios = {
        sunny_afternoon: {
            hour: 14,
            month: 6,
            cloud: 20,
            precipitation_mm: 0,
            humidity: 50,
            visibility_km: 15,
            wind_speed_kph: 10,
            temperature_final: 25
        },
        stormy_night: {
            hour: 20,
            month: 12,
            cloud: 95,
            precipitation_mm: 2.0,
            humidity: 85,
            visibility_km: 3,
            wind_speed_kph: 25,
            temperature_final: 15
        },
        cloudy_morning: {
            hour: 10,
            month: 3,
            cloud: 85,
            precipitation_mm: 0.5,
            humidity: 70,
            visibility_km: 6,
            wind_speed_kph: 12,
            temperature_final: 20
        },
        foggy_evening: {
            hour: 18,
            month: 11,
            cloud: 100,
            precipitation_mm: 0.1,
            humidity: 90,
            visibility_km: 2,
            wind_speed_kph: 5,
            temperature_final: 8
        }
    };

    const scenario = scenarios[type];
    if (scenario) {
        // Update all form values
        Object.keys(scenario).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                element.value = scenario[key];
                // Trigger input event to update displays
                const event = new Event('input');
                element.dispatchEvent(event);
            }
        });
        
        // Show loading briefly to indicate scenario loaded
        const button = document.querySelector('.btn-primary');
        const originalText = button.innerHTML;
        button.innerHTML = '<span class="btn-icon">🎯</span> Scenario Loaded!';
        button.style.background = 'linear-gradient(135deg, #27ae60, #2ecc71)';
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = '';
        }, 2000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.predictor = new StreetlightPredictor();
    
    // Add some interactive effects
    const inputs = document.querySelectorAll('.form-input');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
});

// Global functions for range inputs
function updateHourValue(value) {
    if (window.predictor) window.predictor.updateHourValue(value);
}
function updateCloudValue(value) {
    if (window.predictor) window.predictor.updateCloudValue(value);
}
function updatePrecipValue(value) {
    if (window.predictor) window.predictor.updatePrecipValue(value);
}
function updateHumidityValue(value) {
    if (window.predictor) window.predictor.updateHumidityValue(value);
}
function updateVisibilityValue(value) {
    if (window.predictor) window.predictor.updateVisibilityValue(value);
}
function updateWindValue(value) {
    if (window.predictor) window.predictor.updateWindValue(value);
}
function updateTempValue(value) {
    if (window.predictor) window.predictor.updateTempValue(value);
}
