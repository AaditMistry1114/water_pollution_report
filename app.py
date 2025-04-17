from flask import Flask, render_template, redirect, request, flash, url_for
import mysql.connector
from geopy.geocoders import Nominatim
import folium
import os
from geopy.exc import GeocoderTimedOut


app = Flask(__name__)
app.secret_key = 'mykey123'  # for flash message

# Database connection
db = mysql.connector.connect(
    user="root",
    host="localhost",
    passwd="aadit@2005",
    database="waterquality"
)
my_cursor = db.cursor()

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/map', methods=['GET', 'POST'])
def map_view():
    if request.method == 'POST':
        location_name = request.form.get("location")
        ph = request.form.get("ph")
        color = request.form.get("color")
        contaminants = request.form.get("contaminants")

        if not location_name:
            flash("Please enter a location.", "danger")
            return redirect(url_for("home"))

        try:
            geolocator = Nominatim(user_agent="water_app")
            location = geolocator.geocode(location_name, timeout=10)

            if location is None:
                flash("Location not found. Try a different place.", "danger")
                return redirect(url_for("home"))

            lat, lon = location.latitude, location.longitude

            # Save data to database
            query = "INSERT INTO reports (location_name, latitude, longitude, ph, color, contaminants) VALUES (%s, %s, %s, %s, %s, %s)"
            my_cursor.execute(query, (location_name, lat, lon, ph, color, contaminants))
            db.commit()

            # Create map
            m = folium.Map(location=[lat, lon], zoom_start=13)
            folium.Marker(
                [lat, lon],
                popup=f"Location: {location_name}<br>pH: {ph}<br>Color: {color}<br>Contaminants: {contaminants}",
                icon=folium.Icon(color="blue")
            ).add_to(m)

            map_html = m._repr_html_()
            return render_template("map.html", map_html=map_html)

        except GeocoderTimedOut:
            flash("Geolocation timed out. Try again.", "warning")
            return redirect(url_for("home"))

    # GET method shows default map
    m = folium.Map(location=[20, 0], zoom_start=2)
    map_html = m._repr_html_()
    return render_template("map.html", map_html=map_html)

@app.route('/reports')
def report_lists():
    my_cursor.execute("SELECT id, location_name, ph, color, contaminants FROM reports")
    reports = []
    for (report_id, location_name, ph, color, contaminants) in my_cursor:
        reports.append({
            'id': report_id,
            'location': location_name,
            'ph': ph,
            'color': color,
            'contaminants': contaminants or 'None'
        })
    return render_template('reports.html', reports=reports)

@app.route('/delete/<int:report_id>')
def delete_report(report_id):
    try:
        delete_query = "DELETE FROM reports WHERE id = %s"
        my_cursor.execute(delete_query, (report_id,))
        db.commit()
        flash("Report deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting report: {str(e)}", "danger")
    return redirect(url_for('report_lists'))

@app.route('/update/<int:report_id>', methods=['GET', 'POST'])
def update_report(report_id):
    if request.method == 'POST':
        location = request.form.get('location')
        ph = request.form.get('ph')
        color = request.form.get('color')
        contaminants = request.form.get('contaminants')

        update_query = """
        UPDATE reports
        SET location_name = %s, ph = %s, color = %s, contaminants = %s
        WHERE id = %s
        """
        my_cursor.execute(update_query, (location, ph, color, contaminants, report_id))
        db.commit()
        flash("Report updated successfully!", "success")
        return redirect(url_for('report_lists'))

# Get current report data
    my_cursor.execute("SELECT location_name, ph, color, contaminants FROM reports WHERE id = %s", (report_id,))
    report = my_cursor.fetchone()
    if report:
        report_data = {
        'id': report_id,
        'location': report[0],
        'ph': report[1],
        'color': report[2],
        'contaminants': report[3]
        }
        return render_template("update.html", report=report_data)
    else:
        flash("Report not found.", "danger")
        return redirect(url_for('report_lists'))

@app.route('/contactus', methods=['GET', 'POST'])
def contactus():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        insert_query = "INSERT INTO contact_messages (name, email, subject, message) VALUES (%s, %s, %s, %s)"
        my_cursor.execute(insert_query, (name, email, subject, message))
        db.commit()

        flash("The form has been submitted successfully!", 'success')
        return redirect('/contactus')
    
    return render_template('contactus.html')

if __name__ == "__main__":
    app.run(debug=True, port=8000)