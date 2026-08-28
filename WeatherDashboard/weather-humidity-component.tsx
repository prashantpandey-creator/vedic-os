import React from 'react';

const WeatherHumidityComponent = ({ humidity }) => {
  return (
    <div className="weather-humidity-component">
      <p>Current Humidity: {humidity}%</p>
    </div>
  );
};

export default WeatherHumidityComponent;