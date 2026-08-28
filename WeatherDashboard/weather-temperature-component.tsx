import React from 'react';

const WeatherTemperatureComponent = ({ temperature, unit }) => {
  return (
    <div className="weather-temperature">
      <span>{temperature}</span>
      <span>&deg;{unit}</span>
    </div>
  );
};

export default WeatherTemperatureComponent;