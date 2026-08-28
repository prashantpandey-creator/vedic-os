import React from 'react';
import PropTypes from 'prop-types';

const WeatherWindSpeedComponent = ({ wind_speed }) => {
  return (
    <div className="weather-wind-speed">
      <h3>Current Wind Speed</h3>
      <p>{wind_speed} km/h</p>
    </div>
  );
};

WeatherWindSpeedComponent.propTypes = {
  wind_speed: PropTypes.number.isRequired,
};

export default WeatherWindSpeedComponent;