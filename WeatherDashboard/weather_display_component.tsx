java
import java.awt.*;
import javax.swing.*;

public class WeatherDisplayComponent extends JPanel {
    
    private JLabel temperatureLabel;
    private JLabel conditionLabel;
    private JLabel humidityLabel;
    private JLabel windSpeedLabel;

    public WeatherDisplayComponent(String temperature, String condition, String humidity, String windSpeed) {
        setLayout(new FlowLayout());

        temperatureLabel = new JLabel("Temperature: " + temperature);
        add(temperatureLabel);

        conditionLabel = new JLabel("Condition: " + condition);
        add(conditionLabel);

        humidityLabel = new JLabel("Humidity: " + humidity);
        add(humidityLabel);

        windSpeedLabel = new JLabel("Wind Speed: " + windSpeed);
        add(windSpeedLabel);
    }
}
