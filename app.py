from flask import Flask, render_template, request
import requests
import mysql.connector
import io
import base64
import matplotlib.pyplot as plt
import mysql.connector

app = Flask(__name__)

# Function to establish MySQL database connection
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',  # Default XAMPP password
        database='weather'  # The name of your database
    )
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    weather = None
    forecast = None
    prediction_chart = None
    suggestion = None  # Variable to store weather suggestion
    lat = request.args.get('lat')  # Get latitude from URL
    lon = request.args.get('lon')  # Get longitude from URL
    city = request.form.get('city') if request.method == 'POST' else None  # Get city from form input
    api_key = '8e3c31bd68534ed22ef89668fb06b8b9'

    # Initialize URLs as None
    weather_url = None
    forecast_url = None

    # Check if lat/lon or city is provided, and set appropriate URLs
    if lat and lon:
        weather_url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric'
        forecast_url = f'http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric'
    elif city:
        weather_url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
        forecast_url = f'http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric'

    if weather_url and forecast_url:
        weather_response = requests.get(weather_url)  # Send request to get weather data
        forecast_response = requests.get(forecast_url)  # Send request to get forecast data

        if weather_response.status_code == 200:
            weather_data = weather_response.json()
            weather = {
                'city': weather_data['name'],
                'country': weather_data['sys']['country'],
                'description': weather_data['weather'][0]['description'],
                'temperature': weather_data['main']['temp'],
                'feels_like': weather_data['main']['feels_like'],
                'humidity': weather_data['main']['humidity'],
                'pressure': weather_data['main']['pressure'],
                'latitude': weather_data['coord']['lat'],
                'longitude': weather_data['coord']['lon']
            }

            # Suggestion based on weather conditions
            if weather['temperature'] > 30:
                suggestion = "It's quite hot outside, don't forget to drink water and wear light clothes!"
            elif weather['temperature'] < 10:
                suggestion = "It's cold, make sure to wear warm clothes!"
            elif 'rain' in weather['description']:
                suggestion = "It's rainy outside, don't forget to carry an umbrella!"
            else:
                suggestion = "The weather looks fine, enjoy your day!"

            # Store weather data in MySQL database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(""" 
                INSERT INTO weather_data (city, country, temperature, feels_like, humidity, pressure, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (weather['city'], weather['country'], weather['temperature'], weather['feels_like'],
                  weather['humidity'], weather['pressure'], weather['latitude'], weather['longitude']))
            conn.commit()  # Commit the transaction
            conn.close()

        if forecast_response.status_code == 200:
            forecast_data = forecast_response.json()
            forecast = []
            dates = []  # List for dates
            temps = []  # List for temperatures

            # Extract forecast data for chart
            for day in forecast_data['list']:
                forecast.append({
                    'date': day['dt_txt'],
                    'temp_day': day['main']['temp_max'],
                    'temp_night': day['main']['temp_min']
                })
                dates.append(day['dt_txt'])  # Store date
                temps.append(day['main']['temp_max'])  # Store temperature

            # Generate prediction chart
            plt.figure(figsize=(10, 6))
            plt.plot(dates, temps, marker='o', label='Temperature (°C)')
            plt.title('Weather Prediction')
            plt.xlabel('Date')
            plt.ylabel('Temperature (°C)')
            plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability
            plt.tight_layout()  # Adjust layout
            plt.legend()

            # Save the chart to a PNG image in memory
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            prediction_chart = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()

    return render_template('index.html', weather=weather, forecast=forecast, prediction_chart=prediction_chart, suggestion=suggestion)

if __name__ == '__main__':
    app.run(debug=True)
