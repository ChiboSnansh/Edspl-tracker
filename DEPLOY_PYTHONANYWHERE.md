# PythonAnywhere Deployment Guide

## Step 1: Create Free Account
1. Go to https://www.pythonanywhere.com
2. Click "Start for free" and sign up
3. Note your username (e.g., `edspl`)

## Step 2: Upload Code
Option A - From GitHub (Recommended):
1. Open a Bash console from Dashboard
2. Run: `git clone https://github.com/YOUR_USERNAME/edspl-tracker.git`

Option B - Upload ZIP:
1. Go to Files tab
2. Upload all project files to `/home/YOUR_USERNAME/edspl-tracker/`

## Step 3: Create Virtual Environment
In the Bash console:
```bash
cd ~/edspl-tracker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py
```

## Step 4: Configure Web App
1. Go to **Web** tab
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.10

## Step 5: Set WSGI Configuration
1. Click on the WSGI configuration file link
2. Delete all content and paste:

```python
import sys
import os

project_home = '/home/YOUR_USERNAME/edspl-tracker'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['FLASK_ENV'] = 'production'

from app import app as application
```

3. Replace `YOUR_USERNAME` with your PythonAnywhere username

## Step 6: Set Virtual Environment Path
In Web tab, under "Virtualenv":
- Enter: `/home/YOUR_USERNAME/edspl-tracker/venv`

## Step 7: Set Static Files
Under "Static files":
- URL: `/static/`
- Directory: `/home/YOUR_USERNAME/edspl-tracker/static`

## Step 8: Reload and Access
1. Click green "Reload" button
2. Access at: `https://YOUR_USERNAME.pythonanywhere.com`

---

## Your App URL
After deployment: `https://YOUR_USERNAME.pythonanywhere.com`

## Default Login
- Admin: `admin` / `admin123`
- Change passwords after first login!

## Notes
- Free tier includes 512MB storage
- App sleeps after inactivity (wakes on access)
- Upgrade to paid for always-on and custom domain
