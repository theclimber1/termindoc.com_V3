import json
import os
from datetime import datetime

def generate_dashboard():
    # 1. Load Data
    data_path = os.path.join("data", "appointments.json")
    if not os.path.exists(data_path):
        print("❌ data/appointments.json not found!")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        doctors_data = json.load(f)

    # 2. Prepare Data (Add Lat/Lon placeholders)
    doctors_list = []
    for doc_id, doc in doctors_data.items():
        # Flatten slots to just the first one for sorting, or keep all?
        # The prompt implies sorting doctors by "Next Appointment" or "Distance".
        # So we need the *next* appointment for sorting.
        
        slots = doc.get("slots", [])
        next_slot = None
        if slots:
            # Sort slots to find the earliest one
            sorted_slots = sorted(slots)
            next_slot = sorted_slots[0]
        
        # Add placeholder coordinates if missing
        # In a real app, we would geocode 'doc["address"]' here.
        if "lat" not in doc:
            doc["lat"] = 0.0
        if "lon" not in doc:
            doc["lon"] = 0.0
            
        doc["next_slot"] = next_slot
        doctors_list.append(doc)

    # Serialize to JSON for embedding
    doctors_json = json.dumps(doctors_list, ensure_ascii=False)

    # 3. Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NextDoc Dashboard</title>
    <style>
        :root {{
            --primary: #007bff;
            --bg: #f8f9fa;
            --card-bg: #ffffff;
            --text: #333;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 20px;
            text-align: center;
        }}
        .controls {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 20px;
        }}
        button {{
            padding: 10px 20px;
            border: none;
            border-radius: 20px;
            background-color: #e0e0e0;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.2s;
        }}
        button.active {{
            background-color: var(--primary);
            color: white;
        }}
        button:hover {{
            opacity: 0.9;
        }}
        #loading-spinner {{
            display: none;
            margin-left: 10px;
        }}
        .doctor-card {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .doctor-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .doctor-name {{
            font-size: 1.2em;
            font-weight: bold;
            margin: 0;
        }}
        .doctor-meta {{
            color: #666;
            font-size: 0.9em;
        }}
        .next-slot {{
            background-color: #e3f2fd;
            color: #0d47a1;
            padding: 8px 12px;
            border-radius: 8px;
            font-weight: bold;
            display: inline-block;
            align-self: flex-start;
        }}
        .distance-badge {{
            font-size: 0.85em;
            color: #2e7d32;
            background: #e8f5e9;
            padding: 4px 8px;
            border-radius: 4px;
            margin-left: 10px;
            display: none; /* Hidden by default */
        }}
        .no-slots {{
            color: #999;
            font-style: italic;
        }}
        a.book-btn {{
            display: inline-block;
            background-color: var(--primary);
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 0.9em;
            margin-top: 10px;
            align-self: flex-start;
        }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>NextDoc 🩺</h1>
        <p>Finde deinen nächsten Arzttermin</p>
    </header>

    <div class="controls">
        <button id="btn-time" class="active" onclick="sortByTime()">🕒 Nächster Termin</button>
        <button id="btn-dist" onclick="sortByDistance()">📍 Nächste Entfernung <span id="loading-spinner">⏳</span></button>
    </div>

    <div id="doctor-list">
        <!-- Cards will be injected here -->
    </div>
</div>

<script>
    // Embedded Data
    let doctors = {doctors_json};
    let userLat = null;
    let userLon = null;

    const listEl = document.getElementById('doctor-list');
    const btnTime = document.getElementById('btn-time');
    const btnDist = document.getElementById('btn-dist');
    const spinner = document.getElementById('loading-spinner');

    // Initial Render (Time Sorted)
    sortByTime();

    function renderList(docs) {{
        listEl.innerHTML = '';
        docs.forEach(doc => {{
            const card = document.createElement('div');
            card.className = 'doctor-card';
            
            // Format Next Slot
            let slotHtml = '<span class="no-slots">Keine freien Termine</span>';
            if (doc.next_slot) {{
                const date = new Date(doc.next_slot);
                const fmtDate = date.toLocaleDateString('de-DE', {{ weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' }});
                const fmtTime = date.toLocaleTimeString('de-DE', {{ hour: '2-digit', minute: '2-digit' }});
                slotHtml = `<span class="next-slot">🕒 ${{fmtDate}} um ${{fmtTime}}</span>`;
            }}

            // Distance Badge
            let distHtml = '';
            if (doc.distance !== undefined && doc.distance !== null) {{
                distHtml = `<span class="distance-badge">📍 ${{doc.distance.toFixed(1)}} km</span>`;
            }}

            card.innerHTML = `
                <div class="doctor-header">
                    <div>
                        <h3 class="doctor-name">${{doc.name}} ${{distHtml}}</h3>
                        <div class="doctor-meta">${{doc.speciality}} • ${{doc.address}}</div>
                        <div class="doctor-meta">${{doc.insurance.join(', ')}}</div>
                    </div>
                </div>
                ${{slotHtml}}
                ${{doc.booking_url ? `<a href="${{doc.booking_url}}" target="_blank" class="book-btn">Termin buchen</a>` : ''}}
            `;
            listEl.appendChild(card);
        }});
    }}

    function sortByTime() {{
        setActive(btnTime);
        // Sort: Docs with slots first, then by date. Docs without slots last.
        const sorted = [...doctors].sort((a, b) => {{
            if (!a.next_slot && !b.next_slot) return 0;
            if (!a.next_slot) return 1;
            if (!b.next_slot) return -1;
            return new Date(a.next_slot) - new Date(b.next_slot);
        }});
        renderList(sorted);
    }}

    function sortByDistance() {{
        setActive(btnDist);
        
        if (userLat && userLon) {{
            // Already have location, just sort
            applyDistanceSort();
        }} else {{
            // Request Location
            spinner.style.display = 'inline';
            if (!navigator.geolocation) {{
                alert("Geolokalisierung wird von diesem Browser nicht unterstützt.");
                spinner.style.display = 'none';
                sortByTime();
                return;
            }}

            navigator.geolocation.getCurrentPosition(
                (position) => {{
                    userLat = position.coords.latitude;
                    userLon = position.coords.longitude;
                    spinner.style.display = 'none';
                    applyDistanceSort();
                }},
                (error) => {{
                    console.error("Error getting location:", error);
                    alert("Standortzugriff verweigert oder nicht verfügbar. Sortierung nach Zeit wird beibehalten.");
                    spinner.style.display = 'none';
                    sortByTime();
                }}
            );
        }}
    }}

    function applyDistanceSort() {{
        // Calculate distances
        doctors.forEach(doc => {{
            // Use placeholder 0,0 if missing, but ideally we need real coords
            // If doc.lat is 0, distance will be huge/wrong, but code won't crash.
            doc.distance = getDistanceFromLatLonInKm(userLat, userLon, doc.lat, doc.lon);
        }});

        // Sort by distance
        const sorted = [...doctors].sort((a, b) => a.distance - b.distance);
        renderList(sorted);
    }}

    function setActive(btn) {{
        document.querySelectorAll('.controls button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }}

    // Haversine Formula
    function getDistanceFromLatLonInKm(lat1, lon1, lat2, lon2) {{
        var R = 6371; // Radius of the earth in km
        var dLat = deg2rad(lat2 - lat1);  
        var dLon = deg2rad(lon2 - lon1); 
        var a = 
            Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) * 
            Math.sin(dLon/2) * Math.sin(dLon/2); 
        var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
        var d = R * c; // Distance in km
        return d;
    }}

    function deg2rad(deg) {{
        return deg * (Math.PI/180)
    }}
</script>

</body>
</html>
    """

    # 4. Write Output
    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ dashboard.html generated successfully!")

if __name__ == "__main__":
    generate_dashboard()
