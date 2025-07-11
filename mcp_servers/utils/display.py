"""Display utilities for formatting Open-Meteo weather data output."""


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    NC = '\033[0m'  # No Color


def print_colored(text: str, color: str = Colors.NC) -> None:
    """Print text with specified color."""
    print(f"{color}{text}{Colors.NC}")


def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print_colored(f"{'=' * 60}", Colors.CYAN)
    print_colored(f"{title.center(60)}", Colors.CYAN)
    print_colored(f"{'=' * 60}", Colors.CYAN)
    print()


def print_subsection(title: str) -> None:
    """Print a formatted subsection header."""
    print()
    print_colored(f"--- {title} ---", Colors.YELLOW)
    print()


def print_weather_summary(data: dict, location_name: str = "") -> None:
    """Print formatted weather data summary."""
    if location_name:
        print_colored(f"\nWeather for {location_name}:", Colors.BLUE)
    
    # Current conditions
    if 'current' in data:
        current = data['current']
        units = data.get('current_units', {})
        print("\nCurrent Conditions:")
        
        if 'temperature_2m' in current:
            temp_unit = units.get('temperature_2m', '°C')
            print(f"  Temperature: {current['temperature_2m']}{temp_unit}")
        
        if 'relative_humidity_2m' in current:
            print(f"  Humidity: {current['relative_humidity_2m']}%")
        
        if 'precipitation' in current:
            precip_unit = units.get('precipitation', 'mm')
            print(f"  Precipitation: {current['precipitation']} {precip_unit}")
        
        if 'windspeed_10m' in current:
            wind_unit = units.get('windspeed_10m', 'km/h')
            print(f"  Wind Speed: {current['windspeed_10m']} {wind_unit}")
    
    # Daily forecast
    if 'daily' in data:
        daily = data['daily']
        times = daily.get('time', [])
        
        if times:
            print("\nDaily Forecast:")
            for i in range(min(5, len(times))):  # Show up to 5 days
                date = times[i]
                print(f"\n  {date}:")
                
                if 'temperature_2m_max' in daily and 'temperature_2m_min' in daily:
                    temp_max = daily['temperature_2m_max'][i]
                    temp_min = daily['temperature_2m_min'][i]
                    print(f"    Temperature: {temp_min}°C - {temp_max}°C")
                
                if 'precipitation_sum' in daily:
                    precip = daily['precipitation_sum'][i]
                    print(f"    Precipitation: {precip} mm")


def print_soil_conditions(data: dict) -> None:
    """Print formatted soil moisture and temperature data."""
    print_colored("\nSoil Conditions:", Colors.GREEN)
    
    if 'hourly' in data:
        hourly = data['hourly']
        times = hourly.get('time', [])
        
        if times:
            # Show latest values
            latest_idx = -1
            print(f"\nLatest conditions ({times[latest_idx]}):")
            
            # Soil moisture layers
            moisture_layers = [
                ('soil_moisture_0_to_1cm', '0-1cm'),
                ('soil_moisture_1_to_3cm', '1-3cm'),
                ('soil_moisture_3_to_9cm', '3-9cm'),
                ('soil_moisture_9_to_27cm', '9-27cm'),
                ('soil_moisture_27_to_81cm', '27-81cm')
            ]
            
            print("\n  Soil Moisture (m³/m³):")
            for param, depth in moisture_layers:
                if param in hourly:
                    value = hourly[param][latest_idx]
                    print(f"    {depth}: {value:.3f}")
            
            # Soil temperature layers
            temp_layers = [
                ('soil_temperature_0cm', '0cm'),
                ('soil_temperature_6cm', '6cm'),
                ('soil_temperature_18cm', '18cm'),
                ('soil_temperature_54cm', '54cm')
            ]
            
            print("\n  Soil Temperature (°C):")
            for param, depth in temp_layers:
                if param in hourly:
                    value = hourly[param][latest_idx]
                    print(f"    {depth}: {value:.1f}")


def print_precipitation_summary(data: dict, period_name: str = "") -> None:
    """Print precipitation summary."""
    print_colored(f"\nPrecipitation Summary{' - ' + period_name if period_name else ''}:", Colors.CYAN)
    
    if 'daily' in data:
        daily = data['daily']
        times = daily.get('time', [])
        precip_sums = daily.get('precipitation_sum', [])
        
        if times and precip_sums:
            total_precip = sum(precip_sums)
            avg_precip = total_precip / len(precip_sums)
            max_precip = max(precip_sums)
            max_day = times[precip_sums.index(max_precip)]
            
            print(f"  Total: {total_precip:.1f} mm")
            print(f"  Average: {avg_precip:.1f} mm/day")
            print(f"  Maximum: {max_precip:.1f} mm on {max_day}")
            
            # Count dry days
            dry_days = sum(1 for p in precip_sums if p == 0)
            print(f"  Dry days: {dry_days} out of {len(precip_sums)}")


def print_location_results(locations: list) -> None:
    """Print geocoding search results."""
    print_colored("\nLocation Search Results:", Colors.BLUE)
    
    if not locations:
        print("  No locations found")
        return
    
    for i, loc in enumerate(locations, 1):
        name = loc.get('name', 'Unknown')
        country = loc.get('country', '')
        admin1 = loc.get('admin1', '')  # State/Province
        lat = loc.get('latitude', 0)
        lon = loc.get('longitude', 0)
        
        location_parts = [name]
        if admin1:
            location_parts.append(admin1)
        if country:
            location_parts.append(country)
        
        full_name = ", ".join(location_parts)
        print(f"  {i}. {full_name}")
        print(f"     Coordinates: {lat:.4f}°N, {lon:.4f}°E")


def format_api_error(error: Exception) -> str:
    """Format API error messages for display."""
    error_msg = str(error)
    
    if "404" in error_msg:
        return "Location or data not found"
    elif "429" in error_msg:
        return "Rate limit exceeded - please try again later"
    elif "500" in error_msg:
        return "Server error - please try again later"
    elif "connection" in error_msg.lower():
        return "Connection error - please check your internet connection"
    else:
        return f"API error: {error_msg}"


def print_attribution() -> None:
    """Print Open-Meteo attribution."""
    print_colored("\nWeather data by Open-Meteo.com", Colors.MAGENTA)