import React from 'react';
import WeatherWidget from './WeatherWidget';

const WeatherDashboardPage = ({ location, weatherData }) => {
    return (
        <div className="weather-dashboard-page">
            <h1>Weather Dashboard</h1>
            <p>Current weather for: {location}</p>
            <WeatherWidget weather={weatherData} />
        </div>
    );
};

export default WeatherDashboardPage;