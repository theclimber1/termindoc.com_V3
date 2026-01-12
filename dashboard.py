import streamlit as st
import json
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from core.geocoder import GeocodingService
from core.filter_service import FilterService

# --- Page Config ---
st.set_page_config(
    page_title="NextDoc",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for Redesign 2.0 (Interactive) ---
st.markdown("""
    <style>
    /* Global Variables */
    :root {
        --primary: #008080;
        --secondary: #2c7a7b;
        --bg-soft: #f8f9fa;
        --text-main: #2d3748;
        --card-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* INPUT FOCUS OVERRIDES (Remove Red) */
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="input"] > div:focus-within,
    .stTextInput > div > div:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 1px var(--primary) !important;
    }
    
    /* Button Overrides */
    button[kind="primary"] {
        background-color: var(--primary) !important;
        border-color: var(--primary) !important;
    }
    
    /* Checkbox/Radio Focus */
    .stCheckbox label span:first-child input:checked + div,
    .stRadio label span:first-child input:checked + div {
        background-color: var(--primary) !important;
        border-color: var(--primary) !important;
    }
    
    /* Hero Section Styling */
    .hero-container {
        text-align: center;
        padding: 4rem 1rem;
        background: linear-gradient(135deg, #e6fffa 0%, #ffffff 100%);
        border-radius: 16px;
        margin-bottom: 2rem;
        transition: all 0.5s ease-in-out;
    }
    
    /* Compact Mode for Hero */
    .hero-container.compact {
        padding: 1.5rem 1rem;
        margin-bottom: 1rem;
        background: #f0fdfa; /* Softer background for compact mode */
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--primary);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .hero-container.compact .hero-title {
        font-size: 1.5rem; /* Smaller title */
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        font-size: 1.1rem;
        color: #718096;
        margin-bottom: 2rem;
        transition: all 0.3s ease;
    }
    .hero-container.compact .hero-subtitle {
        display: none; /* Hide subtitle in compact mode */
    }
    
    /* Animation Keyframes */
    @keyframes slideUpFade {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Result Container Animation */
    .results-container-animated {
        animation: slideUpFade 0.6s ease-out forwards;
    }
    
    /* Result Card Styling */
    .result-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: var(--card-shadow);
        margin-bottom: 1rem;
        border-left: 5px solid var(--primary);
        transition: transform 0.2s;
    }
    .result-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Typography Helpers */
    .card-date { font-size: 1.1rem; font-weight: 700; color: var(--text-main); }
    .card-time { font-size: 1.4rem; font-weight: 800; color: var(--primary); }
    .card-doctor { font-size: 1.1rem; font-weight: 600; color: var(--text-main); }
    .card-meta { font-size: 0.9rem; color: #718096; }
    .dist-badge { color: #2f855a; font-weight: 600; font-size: 0.9rem; }
    
    /* Slot Batches */
    .slot-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
    }
    .slot-badge {
        display: inline-flex;
        align-items: center;
        background-color: #f0fdfa;
        color: #008080;
        border: 1px solid #b2f5ea;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        text-decoration: none;
        transition: background-color 0.2s;
    }
    .slot-badge:hover {
        background-color: #e6fffa;
        text-decoration: none;
        border-color: #008080;
    }
    .slot-badge.akut {
        background-color: #fff5f5;
        color: #c53030;
        border-color: #feb2b2;
    }
    .slot-badge.akut:hover {
        background-color: #fed7d7;
    }
    .slot-badge small {
        margin-left: 6px;
        opacity: 0.8;
        font-size: 0.75em;
        text-transform: uppercase;
    }

    /* Mobile Optimizations */
    @media (max-width: 600px) {
        .hero-title { font-size: 1.8rem; }
        .hero-container.compact .hero-title { font-size: 1.3rem; }
        .result-card { padding: 1rem; }
        .card-time { font-size: 1.2rem; }
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp > header {visibility: hidden;}
    
    </style>
""", unsafe_allow_html=True)

# --- State Management ---
if 'search_active' not in st.session_state:
    st.session_state.search_active = False
if 'search_filters' not in st.session_state:
    st.session_state.search_filters = {}

# --- Data Loading & Helpers ---
@st.cache_resource
def get_geocoder():
    return GeocodingService()

@st.cache_data(ttl=60)
def load_data():
    try:
        with open("data/appointments.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {}

def extract_city(address):
    if not address: return "Unbekannt"
    try:
        parts = address.split(",")
        if len(parts) > 1:
            city_part = parts[-1].strip()
            sub_parts = city_part.split(" ", 1)
            if len(sub_parts) > 1 and sub_parts[0].isdigit() and len(sub_parts[0]) == 4:
                return sub_parts[1]
            return city_part
        return address
    except:
        return "Unbekannt"

def normalize_speciality(raw):
    if isinstance(raw, list):
        return ", ".join([normalize_single_speciality(s) for s in raw])
    return normalize_single_speciality(raw)

def normalize_single_speciality(raw):
    if not isinstance(raw, str): return str(raw)
    s = raw.lower()
    if "allgemeinmedizin" in s: return "Allgemeinmedizin"
    if "kinder" in s and "jugend" in s: return "Kinderheilkunde"
    if "frauenheilkunde" in s or "gynäkologie" in s: return "Gynäkologie & Geburtshilfe"
    if "innere medizin" in s: return "Innere Medizin"
    if "orthopädie" in s: return "Orthopädie"
    if "hno" in s or "hals" in s: return "HNO"
    if "zahn" in s or "kiefer" in s: return "Zahnmedizin / Kieferorthopädie"
    if "kardiologie" in s: return "Innere Medizin (Kardiologie)"
    return raw

def classify_service(name):
    """Classifies a service name into Akut, Vorsorge, or Sonstiges (Currently all gray)."""
    return "Sonstiges", "gray"

def consolidate_data(doctors_json):
    """
    Consolidates granular doctor entries (Dr. X Akut, Dr. X Checkup) into single Grouped objects.
    Returns a list of dicts representing unique Doctors/Groups with aggregated slots.
    """
    aggregated_doctors = {}
    
    for doc_id, doc in doctors_json.items():
        # Identify Group ID
        group_key = doc.get("group_id")
        if not group_key:
            # Fallback: Use Name but strip suffixes like " | Akut" if present
            raw_name = doc.get("name", "Unknown")
            group_key = raw_name.split("|")[0].strip() if "|" in raw_name else raw_name
        
        if group_key not in aggregated_doctors:
            aggregated_doctors[group_key] = {
                "name": group_key,
                "speciality": normalize_speciality(doc.get("speciality", "")),
                "address": doc.get("address", ""),
                "insurance": doc.get("insurance", []),
                "booking_url": doc.get("booking_url"), # Default URL
                "latitude": doc.get("latitude"),
                "longitude": doc.get("longitude"),
                "slots": []
            }
        
        # Determine Service Name for this entry if slots are flat
        base_service_name = "Termin"
        if " | " in doc.get("name", ""):
            base_service_name = doc.get("name").split(" | ")[1]
        
        def add_appt(slot_str, s_name):
            try:
                if slot_str.endswith("Z"):
                    dt = datetime.fromisoformat(slot_str.replace("Z", "+00:00"))
                else:
                    dt = datetime.fromisoformat(slot_str)
                if dt.tzinfo is not None:
                    dt = dt.astimezone()
                dt_naive = dt.replace(tzinfo=None)
                
                # Avoid duplicates (day, time) - since we don't distinguish services anymore
                slot_key = f"{dt_naive.isoformat()}"
                if any(s["datetime"] == dt_naive for s in aggregated_doctors[group_key]["slots"]):
                    return

                category, color = classify_service(s_name)
                aggregated_doctors[group_key]["slots"].append({
                    "datetime": dt_naive,
                    "time_str": dt_naive.strftime("%H:%M"),
                    "date_str": dt_naive.strftime("%d.%m.%Y"),
                    "day_name": dt_naive.strftime("%a"),
                    "service_name": s_name,
                    "category": category,
                    "color": color, 
                    "booking_url": doc.get("booking_url", aggregated_doctors[group_key]["booking_url"])
                })
            except ValueError:
                pass

        # Collect slots from appointment_types or flat slots
        app_types = doc.get("appointment_types", [])
        has_typed_slots = False
        for t in app_types:
            if t.get("slots"):
                label = t.get("name", base_service_name)
                for s in t.get("slots", []):
                    add_appt(s, label)
                has_typed_slots = True
        
        if not has_typed_slots:
            for s in doc.get("slots", []):
                add_appt(s, base_service_name)
                
    # Convert to list and post-process
    result_doctors = []
    for key, data in aggregated_doctors.items():
        if data["slots"]:
            # Sort slots by time
            data["slots"].sort(key=lambda x: x["datetime"])
            # Calculate next available slot
            data["next_slot"] = data["slots"][0]["datetime"]
            result_doctors.append(data)
            
    # Sort doctors by earliest available slot by default (render_results will do final sort)
    result_doctors.sort(key=lambda x: x["next_slot"])
    return result_doctors

# --- Component: Smooth Scroll Script ---
def inject_smooth_scroll():
    # Helper script to scroll to 'results-anchor'
    components.html(
        """
        <script>
            // Wait a moment for the DOM to update with new results
            setTimeout(function() {
                var element = window.parent.document.getElementById('results-anchor');
                if (element) {
                    element.scrollIntoView({behavior: 'smooth', block: 'start'});
                }
            }, 300);
        </script>
        """,
        height=0,
        width=0
    )


# --- Phase 1: Hero Search (Merged Logic) ---
def render_hero(all_doctors, compact=False):
    # Prepare lists (from doctors, not appointments)
    available_specialities = sorted(list(set(d["speciality"] for d in all_doctors if d["speciality"])))
    
    # Dynamic CSS class based on state
    hero_class = "hero-container compact" if compact else "hero-container"
    hero_title = "Finde deinen Arzttermin" if not compact else "Suche verfeinern"
    
    st.markdown(f'<div class="{hero_class}">', unsafe_allow_html=True)
    if not compact:
        st.markdown(f'<div class="hero-title">{hero_title}</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">Schnell, einfach und in deiner Nähe.</div>', unsafe_allow_html=True)
    else:
         # Minimal header in compact
         st.markdown(f'<div class="hero-title" style="font-size:1.2rem; margin-bottom:0;">{hero_title}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
    # Use a container for inputs that persists
    with st.container():
        # Restore previous values if active
        defaults = st.session_state.search_filters if compact else {}
        
        # Row 1
        c1, c2 = st.columns([2, 1])
        with c1:
            selected_specs = st.multiselect(
                "Was suchst du?",
                options=available_specialities,
                placeholder="Fachrichtung wählen",
                default=defaults.get("specialities", [])
            )
        # Terminart filter removed

        # Row 2
        col_loc, col_ins = st.columns([1, 1])
        with col_loc:
            location_def = defaults.get("location", "9020 Klagenfurt")
            location_input = st.text_input("Wo?", value=location_def, placeholder="PLZ oder Stadt")
            
        with col_ins:
            ins_def_idx = 0
            modes = ["Alle Kassen", "Nur Kasse (ÖGK etc.)", "Wahlarzt/Privat"]
            if defaults.get("insurance_mode") in modes:
                ins_def_idx = modes.index(defaults["insurance_mode"])
                    
            insurance_mode = st.selectbox(
                "Versicherung",
                modes,
                index=ins_def_idx
            )
            
        # Spacer
        st.write("")
        
        # Primary Action
        if st.button("🔍 Termine finden", type="primary", use_container_width=True):
            # Save state
            st.session_state.search_filters = {
                "specialities": selected_specs,
                "location": location_input,
                "insurance_mode": insurance_mode,
                "date_range": (datetime.now().date(), datetime.now().date() + timedelta(days=365))
            }
            st.session_state.search_active = True
            st.rerun()

# --- Phase 2: Results View (Below Hero) ---
def render_results(all_doctors):
    filters = st.session_state.search_filters
    
    # Anchor for Scroll
    st.markdown('<div id="results-anchor"></div>', unsafe_allow_html=True)
    
    # Inject JS to scroll to this anchor
    inject_smooth_scroll()
    
    # Wrapper with Animation Class
    st.markdown('<div class="results-container-animated">', unsafe_allow_html=True)

    # 1. Geocoding
    user_coords = None
    if filters["location"]:
        geocoder = get_geocoder()
        user_coords = geocoder.geocode_address(filters["location"])
    
    start_date = filters["date_range"][0]
    end_date = filters["date_range"][1]
    public_insurances = {"ÖGK", "BVAEB", "SVS", "SVS-GW", "SVS-LW", "KFA", "Alle Kassen"}

    filtered_doctors = []
    
    for doc in all_doctors:
        # Doctor Level Filters
        if filters["specialities"]:
            doc_specs = [s.strip() for s in doc["speciality"].split(",")]
            if not any(s in filters["specialities"] for s in doc_specs):
                continue

        doc_insurances = set(doc["insurance"])
        if filters["insurance_mode"] == "Nur Kasse (ÖGK etc.)":
             if not (doc_insurances & public_insurances):
                 continue
        elif filters["insurance_mode"] == "Wahlarzt/Privat":
             if "Wahlarzt" not in doc_insurances and "Privat" not in doc_insurances:
                 continue
                 
        # Location Distance
        if user_coords and user_coords[0]:
            if doc["latitude"] and doc["longitude"]:
                fs = FilterService()
                doc["distance"] = fs.haversine_distance(user_coords[0], user_coords[1], doc["latitude"], doc["longitude"])
            else:
                doc["distance"] = float('inf')
        
        # Slot Level Filter (Date range and Category)
        valid_slots = []
        for slot in doc["slots"]:
            if (start_date <= slot["datetime"].date() <= end_date):
                valid_slots.append(slot)
        
        if valid_slots:
            doc_to_show = doc.copy()
            doc_to_show["slots"] = valid_slots
            doc_to_show["next_slot"] = valid_slots[0]["datetime"]
            filtered_doctors.append(doc_to_show)

    # --- Filter Expander & Sorting ---
    with st.expander("🛠️ Sortierung & Zeitraum anpassen", expanded=False):
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            sort_val = st.radio("Sortierung", ["Datum (früheste zuerst)", "Entfernung (nächste zuerst)"], key="sort_radio")
        with c_f2:
            # Date Range Logic
            range_options = { "Alles": 365, "Nächste 2 Wochen": 14, "Nächste 4 Wochen": 28, "Nächste 2 Monate": 60 }
            current_days = (filters["date_range"][1] - filters["date_range"][0]).days
            closest_key = "Alles"
            for k, v in range_options.items():
                if abs(v - current_days) < 5: closest_key = k
                
            selected_range_key = st.selectbox("Zeitraum", list(range_options.keys()), index=list(range_options.keys()).index(closest_key))
            new_days = range_options[selected_range_key]
            today = datetime.now().date()
            if new_days != current_days:
                 st.session_state.search_filters["date_range"] = (today, today + timedelta(days=new_days))
                 st.rerun()

    # Apply Sorting
    if sort_val == "Entfernung (nächste zuerst)":
        filtered_doctors.sort(key=lambda x: x.get("distance", float('inf')))
    else:
        filtered_doctors.sort(key=lambda x: x["next_slot"])

    # --- Display ---
    st.markdown(f"**{len(filtered_doctors)} Ärzte** mit Terminen in {filters['location']}")
        
    if not filtered_doctors:
         st.info("Keine Termine gefunden. Versuche es mit einem anderen Zeitraum, Ort oder Filter.")
         st.markdown('</div>', unsafe_allow_html=True)
         return

    for doc in filtered_doctors:
        with st.container():
            dist_text = ""
            if "distance" in doc and doc["distance"] < 1000: 
                 dist_text = f"📍 {doc['distance']:.1f} km"
            
            badges = " ".join([f"<span class='badge' style='background:#e2e8f0; color:#4a5568; padding:2px 6px; border-radius:4px; font-size:0.8em; margin-right:4px;'>{i}</span>" for i in doc["insurance"][:3]])
            
            # Slots rendering
            slots_html = ""
            visible_slots = doc["slots"][:5]
            hidden_slots = doc["slots"][5:]
            
            def format_slot(s):
                color_map = {"red": "#e53e3e", "green": "#38a169", "gray": "#718096"}
                bg_color = color_map.get(s["color"], "#718096")
                return f"""
<div style="display:flex; justify-content:space-between; align-items:center; background:#f7fafc; padding:8px; border-radius:6px; margin-bottom:4px; border-left:4px solid {bg_color};">
    <div>
        <span style="font-weight:bold; color:#2d3748;">{s['day_name']} {s['date_str']}</span>
        <span style="font-weight:800; color:{bg_color}; margin-left:8px;">{s['time_str']}</span>
        <span style="font-size:0.85em; color:#718096; margin-left:8px;">{s['service_name']}</span>
    </div>
    <a href="{s['booking_url']}" target="_blank" style="text-decoration:none; color:white; background:{bg_color}; padding:4px 12px; border-radius:12px; font-size:0.8em; font-weight:bold;">Buchen</a>
</div>"""

            slots_html = "".join([format_slot(s) for s in visible_slots])
            
            if hidden_slots:
                hidden_html = "".join([format_slot(s) for s in hidden_slots])
                slots_html += f"""
<details style="margin-top:8px; cursor:pointer;">
    <summary style="text-align:center; font-size:14px; color:#3182ce; font-weight:600; list-style:none; padding:8px; background:#ebf8ff; border-radius:6px;">
        + {len(hidden_slots)} weitere Termine anzeigen
    </summary>
    <div style="margin-top:8px;">
        {hidden_html}
    </div>
</details>"""
 
            st.html(f"""
<div class="result-card">
    <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:12px;">
        <div>
            <div class="card-doctor">{doc['name']}</div>
            <div class="card-meta">{doc['speciality']} • {doc['address']}</div>
            <div class="card-meta" style="margin-top:4px;">{dist_text}</div>
            <div style="margin-top:8px;">{badges}</div>
        </div>
    </div>
    <div>
        {slots_html}
    </div>
</div>
""")
            
    st.markdown('</div>', unsafe_allow_html=True)
 
# --- Main Logic ---
def main():
    raw_data = load_data()
    all_doctors = consolidate_data(raw_data)
    
    # Always render Hero
    render_hero(all_doctors, compact=st.session_state.search_active)
    
    # Render Results BELOW Hero if active
    if st.session_state.search_active:
        render_results(all_doctors)
 
if __name__ == "__main__":
    main()

