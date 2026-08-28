
import React, { useState } from 'react';

const WeatherInputComponent = () => {
  const [location, setLocation] = useState('');
  const onSubmit = (event) => {
    // Call API or perform action with the entered location
    console.log('Submit: ', location);
    event.preventDefault();
  };

  return (
    <div className="weather-input-container">
      <form>
        <input
          type="text"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Enter a location"
        />
        <button onClick={onSubmit}>Search</button>
      </form>
    </div>
  );
};

export default WeatherInputComponent;
