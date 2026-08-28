import React from 'react';

const WeatherDescriptionComponent = ({ description }) => {
  return (
    <div className="weather-description">
      {description}
    </div>
  );
};

export default WeatherDescriptionComponent;