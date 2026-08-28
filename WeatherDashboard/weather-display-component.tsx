import React from 'react';
import ReactDOM from 'react-dom';

const WeatherDisplayComponent = ({ temperature, description, icon }) => {
  return (
    <div className="weather-display-component">
      <h1>{temperature}°C</h1>
      <p>{description}</p>
      <img src={icon} alt="Weather Icon" />
    </div>
  );
};

export default WeatherDisplayComponent;