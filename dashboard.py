import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(
    page_title="NextDoc",
    page_icon="🩺",
    layout="centered"
)

# --- Custom CSS for "Medical Design" ---
st.markdown("""
    <style>
    /* Global Font & Colors */
    :root {
        --primary-color: #008080; /* Teal */
        --secondary-color: #2c7a7b;
        --accent-color: #e6fffa;
        --text-color: #2d3748;
        --light-gray: #f7fafc;
        --button-green: #48bb78;
    }
    
    /* Sidebar Multiselect Tag Color Override */
    span[data-baseweb="tag"] {
        background-color: var(--primary-color) !important;
    }
    
    /* Input Focus Border Override (Remove Red Border) */
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="input"] > div:focus-within {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 1px var(--primary-color) !important;
    }
    
    /* Card Container Styling (Simulated via Column Styling) */
    .appointment-row {
        padding: 10px 0;
        border-radius: 8px;
        transition: background-color 0.2s;
    }
    .appointment-row:hover {
        background-color: var(--light-gray);
    }

    /* Typography */
    .date-col {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-color);
        line-height: 1.2;
    }
    .day-name {
        font-size: 0.85rem;
        font-weight: 500;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .time-col {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--primary-color);
    }
    
    .doctor-col {
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--text-color);
    }
    
    .info-col {
        font-size: 0.9rem;
        color: #4a5568;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: var(--accent-color);
        color: var(--secondary-color);
        margin-right: 5px;
        margin-bottom: 5px;
        border: 1px solid #b2f5ea;
    }

    /* Button Styling Override */
    div[data-testid="stLinkButton"] > a {
        background-color: #48bb78 !important;
        border-color: #48bb78 !important;
        color: white !important;
        font-weight: 600;
        border-radius: 6px;
        box-shadow: 0 2px 4px rgba(72, 187, 120, 0.2);
        transition: all 0.2s;
    }
    div[data-testid="stLinkButton"] > a:hover {
        background-color: #38a169 !important;
        border-color: #38a169 !important;
        box-shadow: 0 4px 6px rgba(72, 187, 120, 0.3);
        transform: translateY(-1px);
    }
    
    /* Remove default Streamlit padding for cleaner look */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Data Loading & Processing ---
@st.cache_data(ttl=60)
def load_data():
    try:
        with open("data/appointments.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {}

def extract_city(address):
    """
    Extracts the city from an address string like 'Street 1, 1234 City'.
    Assumes the city is the last part after a comma, and removes the PLZ.
    """
    if not address:
        return "Unbekannt"
    
    try:
        # Split by comma to get the last part (City + PLZ)
        parts = address.split(",")
        if len(parts) > 1:
            city_part = parts[-1].strip()
            # Remove PLZ (4 digits) if present at the start
            # Example: "9020 Klagenfurt" -> "Klagenfurt"
            # Example: "8062 Kumberg (bei Graz)" -> "Kumberg (bei Graz)"
            
            # Simple heuristic: split by space, if first part is numeric, drop it
            sub_parts = city_part.split(" ", 1)
            if len(sub_parts) > 1 and sub_parts[0].isdigit() and len(sub_parts[0]) == 4:
                return sub_parts[1]
            return city_part
        return address # Fallback
    except:
        return "Unbekannt"

def flatten_data(doctors_json):
    """
    Flattens the hierarchical doctor -> slots structure into a list of appointment objects.
    """
    appointments = []
    
    for doc_id, doc in doctors_json.items():
        # Basic doctor info
        name = doc.get("name", "Unbekannt")
        speciality = doc.get("speciality", "Allgemein")
        address = doc.get("address", "")
        insurance = doc.get("insurance", [])
        booking_url = doc.get("booking_url", "")
        city = extract_city(address)
        
        for slot_str in doc.get("slots", []):
            try:
                # Handle ISO format (sometimes with Z, sometimes without)
                if slot_str.endswith("Z"):
                    dt = datetime.fromisoformat(slot_str.replace("Z", "+00:00"))
                else:
                    dt = datetime.fromisoformat(slot_str)
                
                # Convert to local time (Europe/Vienna) if timezone aware
                if dt.tzinfo is not None:
                    # Simple fixed offset for CET/CEST approximation or use pytz/zoneinfo if available
                    # Since we don't want to add heavy deps if not needed, we can use a simple +1/+2 logic
                    # But better to use astimezone() which uses system local time if no argument
                    # Assuming the server runs in the correct local time or we force it.
                    # Let's try converting to system local time first.
                    dt = dt.astimezone()

                # Convert to naive for display/filtering
                dt_naive = dt.replace(tzinfo=None)
                
                appointments.append({
                    "datetime": dt_naive,
                    "time_str": dt_naive.strftime("%H:%M"),
                    "date_str": dt_naive.strftime("%d.%m.%Y"),
                    "day_name": dt_naive.strftime("%a"), # Short day name
                    "doctor_name": name,
                    "speciality": speciality,
                    "address": address,
                    "insurance": insurance,
                    "booking_url": booking_url,
                    "doctor_id": doc_id,
                    "city": city
                })
            except ValueError:
                continue
                
    # Sort by datetime
    appointments.sort(key=lambda x: x["datetime"])
    return appointments

# --- Sidebar Filters (Outside Fragment) ---
def render_sidebar(all_appointments):
    st.sidebar.header("Filter")
    
    # 1. Speciality
    available_specialities = sorted(list(set(a["speciality"] for a in all_appointments)))
    selected_specialities = st.sidebar.multiselect(
        "Fachrichtung",
        options=available_specialities,
        default=available_specialities
    )
    
    # 2. Insurance
    all_insurances = set()
    for a in all_appointments:
        for ins in a["insurance"]:
            all_insurances.add(ins)
    available_insurances = sorted(list(all_insurances))
    
    selected_insurances = st.sidebar.multiselect(
        "Versicherung",
        options=available_insurances,
        default=[]
    )
    
    # 3. Location (Standort)
    available_cities = sorted(list(set(a["city"] for a in all_appointments)))
    selected_cities = st.sidebar.multiselect(
        "Standort",
        options=available_cities,
        default=[]
    )
    
    # 3. Date Range
    today = datetime.now().date()
    default_end = today + timedelta(days=14)
    
    date_range = st.sidebar.date_input(
        "Zeitraum",
        value=(today, default_end),
        min_value=today,
        format="DD.MM.YYYY"
    )
    
    return {
        "specialities": selected_specialities,
        "insurances": selected_insurances,
        "cities": selected_cities,
        "date_range": date_range
    }

# --- Main Content Fragment (Auto-Reloading) ---
@st.fragment(run_every=10)
def render_content(filters):
    # Reload data inside fragment to get updates
    raw_data = load_data()
    all_appointments = flatten_data(raw_data)
    
    if not all_appointments:
        st.warning("Keine Termine geladen. Bitte warten Sie auf den Scraper.")
        return

    filtered_appointments = []
    
    start_date = filters["date_range"][0]
    end_date = filters["date_range"][1] if len(filters["date_range"]) > 1 else start_date
    
    for appt in all_appointments:
        # Speciality Filter
        if filters["specialities"] and appt["speciality"] not in filters["specialities"]:
            continue
            
        # Insurance Filter
        if filters["insurances"]:
            has_match = any(ins in appt["insurance"] for ins in filters["insurances"])
            if not has_match:
                continue
                
        # Location Filter
        if filters["cities"] and appt["city"] not in filters["cities"]:
            continue
        
        # Date Filter
        appt_date = appt["datetime"].date()
        if not (start_date <= appt_date <= end_date):
            continue
            
        filtered_appointments.append(appt)

    # --- Results Display ---
    st.markdown(f"**{len(filtered_appointments)} Termine gefunden**")
    st.markdown("---") # Top separator
    
    if not filtered_appointments:
        st.info("Keine Termine für die gewählten Filter gefunden.")
        return

    for appt in filtered_appointments:
        # Clean Row Layout
        # We use a container to group, but no broken HTML wrappers.
        # We rely on st.columns for grid layout.
        
        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1, 2.5, 2.5, 2, 1.5])
            
            with c1:
                # Date with styled day name
                st.markdown(f"<div class='date-col'>{appt['date_str']}<br><span class='day-name'>{appt['day_name']}</span></div>", unsafe_allow_html=True)
            
            with c2:
                st.markdown(f"<div class='time-col'>{appt['time_str']}</div>", unsafe_allow_html=True)
                
            with c3:
                st.markdown(f"<div class='doctor-col'>{appt['doctor_name']}</div>", unsafe_allow_html=True)
                
            with c4:
                st.markdown(f"<div class='info-col'>{appt['speciality']}<br>{appt['address']}</div>", unsafe_allow_html=True)
                
            with c5:
                badges_html = ""
                for ins in appt["insurance"]:
                    badges_html += f"<span class='badge'>{ins}</span>"
                st.markdown(badges_html, unsafe_allow_html=True)
                
            with c6:
                if appt["booking_url"]:
                    st.link_button(
                        label="Buchen",
                        url=appt["booking_url"],
                        type="primary",
                        use_container_width=True
                    )
                else:
                    st.button("Belegt", disabled=True, key=f"btn_{appt['doctor_id']}_{appt['datetime']}")
            
            st.divider()

def main():
    st.set_page_config(
        page_title="NextDoc",
        page_icon="🩺",
        layout="wide"
    )
    
    st.title("🩺 NextDoc")
    
    # Initial data load for sidebar
    raw_data = load_data()
    all_appointments = flatten_data(raw_data)
    
    # Render Sidebar
    filters = render_sidebar(all_appointments)
    
    # Render Content
    render_content(filters)

if __name__ == "__main__":
    main()
