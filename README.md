# Medical Appointment Aggregator

This project aggregates medical appointment slots from various sources (Latido, Medineum, Wisitor, etc.) and displays them in a dashboard.

## Prerequisites

Ensure you have Python 3.11+ installed.

Install the required dependencies:

```bash
pip install -r requirements.txt
```

*Note: You may need to install Playwright browsers if not already installed:*
```bash
playwright install
```

## Running the Scraper

The scraper fetches appointment data from the configured doctors and saves it to the database/JSON files.

To run the scraper:

1.  Navigate to the `med-aggregator` directory:
    ```bash
    cd med-aggregator
    ```

2.  Run the main script:
    ```bash
    python3 main.py
    ```

This will:
*   Load doctors from `config/doctors_registry.json`.
*   Run all configured scrapers in parallel.
*   Update the database with found slots.

## Starting the Dashboard

The dashboard provides a web interface to view the aggregated appointments.

To start the dashboard:

1.  Run the Flask app:
    ```bash
    streamlit run dashboard.py
    ```

2.  Open your browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Configuration

*   **Doctors Registry**: `med-aggregator/config/doctors_registry.json`
    *   Add or modify doctors here.
    *   Supported scraper types: `latido`, `medineum`, `kutschera`, `custom_palasser`, `custom_aichinger`, `custom_perfect_smile`.

## Troubleshooting

*   **Missing Dependencies**: If you see `ModuleNotFoundError`, ensure you ran `pip install -r requirements.txt`.
*   **Browser Issues**: If Playwright fails, try running `playwright install`.


ToDO:

test https://www.sporthos.at/team
heide lechner
