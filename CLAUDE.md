# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EDSPL Technical Support Tracker - A compliance-ready ticketing system for Enrich Data Services' technical team. Built with Flask, SQLite, and Bootstrap 5. Deployed on PythonAnywhere.

**Live URL:** https://chibosnansh.pythonanywhere.com

## Commands

```bash
# Setup (first time)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py

# Run locally
source venv/bin/activate
python app.py
# Access at http://localhost:5001

# Add a new user via Python shell
python -c "
from app import app, db
from models import User
with app.app_context():
    user = User(username='newuser', full_name='Name', email='email@edspl.net', role='technician')
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
"
```

## Architecture

### Core Files
- `app.py` - Flask application with all routes (authentication, tickets, comments, attachments, audit log)
- `models.py` - SQLAlchemy models: User, Ticket, Comment, Attachment, ActivityLog
- `config.py` - Configuration (database path, upload settings, allowed file types)
- `init_db.py` - Database initialization with default users

### Database Schema
- **Users**: admin/technician roles with hashed passwords
- **Tickets**: EDSPL-YYYY-NNNN format, status (open/in_progress/resolved/closed), priority, category
- **Comments**: User comments on tickets
- **Attachments**: File uploads stored with UUID filenames in `/uploads`
- **ActivityLog**: Immutable audit trail of all ticket actions

### Templates
- `base.html` - Layout with navbar, Enrich branding (navy #1e3a5f, cyan #06b6d4)
- `login.html`, `dashboard.html`, `audit.html`
- `tickets/` - list.html, create.html, view.html

### Key Patterns
- All routes use `@login_required` decorator
- Activity logging via `log_activity()` helper in models.py
- Template filters: `timeago`, `status_badge`, `priority_badge`
- File uploads use UUID filenames, original names stored in DB

## PythonAnywhere Deployment

WSGI file: `/var/www/chibosnansh_pythonanywhere_com_wsgi.py`
Project path: `/home/chibosnansh/Edspl-tracker`
Virtualenv: `/home/chibosnansh/Edspl-tracker/venv`

To redeploy after changes:
1. SSH/console: `cd ~/Edspl-tracker && git pull`
2. Web tab → Reload

## Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| vijay | vijay123 | admin |
| sanjeev | sanjeev123 | admin |
| tech1 | tech123 | technician |
| tech2 | tech123 | technician |
| tech3 | tech123 | technician |
