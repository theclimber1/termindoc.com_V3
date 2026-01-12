# Deploying the Medical Appointment Finder

Since this project uses **Streamlit**, it cannot be hosted on GitHub Pages (which only supports static HTML/CSS/JS). The best way to host it for free is using **Streamlit Community Cloud**, which integrates directly with your GitHub repository.

## Prerequisites
1. Ensure your code is pushed to GitHub.
2. You have a [Streamlit Community Cloud account](https://share.streamlit.io/) (you can sign in with GitHub).

## Steps to Deploy

1. **Log in to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io/) and sign in.

2. **Create a New App**
   - Click the "New app" button.
   - Select "Use existing repo".

3. **Configure the App**
   - **Repository**: Select your repository (e.g., `your-username/medical-termin-finder`).
   - **Branch**: Select `main` (or `master`).
   - **Main file path**: Enter `dashboard.py`.
   - **App URL**: You can customize the subdomain (e.g., `medical-termin-finder.streamlit.app`).

4. **Deploy!**
   - Click **Deploy**.
   - Streamlit will install the dependencies from `requirements.txt` and start the app.

## Automated Updates
- The **GitHub Actions** workflow (`.github/workflows/update_appointments.yml`) is configured to run every 2 hours.
- It will run `main.py`, update `data/appointments.json`, and push the changes back to the repository.
- **Streamlit Cloud** detects the commit and automatically refreshes the app (or you can use `st.cache_data` with a TTL to fetch the file periodically if it isn't a full reboot).
   - *Note*: By default, Streamlit re-runs the script on update.

## Troubleshooting
- **Secrets**: If your scrapers need API keys/passwords, go to your App Settings on Streamlit Cloud -> **Secrets** and add them there (and also in GitHub Repository Settings -> Secrets for the Action).
- **Logs**: If the automated update fails, check the "Actions" tab in your GitHub repository.
