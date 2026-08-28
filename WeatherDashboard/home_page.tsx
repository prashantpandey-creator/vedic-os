
public class HomePage extends Page {
    public static final String ID = "home_page";
    public static final String ROUTE = "/";
    
    @Override
    public void init() {
        setPageType(PageType.DASHBOARD);
        setDescription("The main dashboard page that displays current weather data for a location.");
        
        // Initialize UI components and add them to the page here.
    }
}
