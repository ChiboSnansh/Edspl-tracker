import os
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Ticket, Comment, Attachment, ActivityLog, log_activity

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# -------------------- Authentication Routes --------------------

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# -------------------- Dashboard --------------------

@app.route('/dashboard')
@login_required
def dashboard():
    # Get ticket statistics
    stats = {
        'total': Ticket.query.count(),
        'open': Ticket.query.filter_by(status='open').count(),
        'in_progress': Ticket.query.filter_by(status='in_progress').count(),
        'resolved': Ticket.query.filter_by(status='resolved').count(),
        'closed': Ticket.query.filter_by(status='closed').count(),
        'my_assigned': Ticket.query.filter_by(assigned_to=current_user.id).filter(Ticket.status.in_(['open', 'in_progress'])).count(),
    }

    # Recent tickets
    recent_tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(10).all()

    # Recent activity
    recent_activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(15).all()

    return render_template('dashboard.html', stats=stats, recent_tickets=recent_tickets, recent_activity=recent_activity)


# -------------------- Ticket Routes --------------------

@app.route('/tickets')
@login_required
def ticket_list():
    # Get filter parameters
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    category = request.args.get('category', '')
    assigned = request.args.get('assigned', '')
    search = request.args.get('search', '')

    query = Ticket.query

    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if category:
        query = query.filter_by(category=category)
    if assigned == 'me':
        query = query.filter_by(assigned_to=current_user.id)
    if assigned == 'unassigned':
        query = query.filter_by(assigned_to=None)
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Ticket.ticket_number.ilike(search_term),
                Ticket.title.ilike(search_term),
                Ticket.description.ilike(search_term)
            )
        )

    tickets = query.order_by(Ticket.created_at.desc()).all()
    users = User.query.all()

    return render_template('tickets/list.html', tickets=tickets, users=users)


@app.route('/tickets/new', methods=['GET', 'POST'])
@login_required
def ticket_create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'medium')
        category = request.form.get('category', 'other')
        assigned_to = request.form.get('assigned_to')

        if not title:
            flash('Title is required.', 'danger')
            return redirect(url_for('ticket_create'))

        ticket = Ticket(
            ticket_number=Ticket.generate_ticket_number(),
            title=title,
            description=description,
            priority=priority,
            category=category,
            created_by=current_user.id,
            assigned_to=int(assigned_to) if assigned_to else None
        )
        db.session.add(ticket)
        db.session.commit()

        # Log creation
        log_activity(ticket.id, current_user.id, 'created')
        if ticket.assigned_to:
            assignee = User.query.get(ticket.assigned_to)
            log_activity(ticket.id, current_user.id, 'assigned', None, assignee.full_name)
        db.session.commit()

        flash(f'Ticket {ticket.ticket_number} created successfully.', 'success')
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    users = User.query.all()
    return render_template('tickets/create.html', users=users)


@app.route('/tickets/<int:ticket_id>')
@login_required
def ticket_view(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    users = User.query.all()
    return render_template('tickets/view.html', ticket=ticket, users=users)


@app.route('/tickets/<int:ticket_id>/update', methods=['POST'])
@login_required
def ticket_update(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    # Track changes for audit
    old_status = ticket.status
    old_priority = ticket.priority
    old_assignee = ticket.assignee.full_name if ticket.assignee else None

    # Update fields
    new_status = request.form.get('status')
    new_priority = request.form.get('priority')
    new_assigned_to = request.form.get('assigned_to')
    new_title = request.form.get('title', '').strip()
    new_description = request.form.get('description', '').strip()

    if new_title:
        ticket.title = new_title
    if new_description is not None:
        ticket.description = new_description
    if new_status:
        ticket.status = new_status
    if new_priority:
        ticket.priority = new_priority

    ticket.assigned_to = int(new_assigned_to) if new_assigned_to else None
    ticket.updated_at = datetime.utcnow()

    if new_status == 'resolved' and old_status != 'resolved':
        ticket.resolved_at = datetime.utcnow()

    db.session.commit()

    # Log changes
    if old_status != ticket.status:
        log_activity(ticket.id, current_user.id, 'status_changed', old_status, ticket.status)
    if old_priority != ticket.priority:
        log_activity(ticket.id, current_user.id, 'priority_changed', old_priority, ticket.priority)

    new_assignee = ticket.assignee.full_name if ticket.assignee else None
    if old_assignee != new_assignee:
        log_activity(ticket.id, current_user.id, 'assigned', old_assignee, new_assignee)

    db.session.commit()

    flash('Ticket updated successfully.', 'success')
    return redirect(url_for('ticket_view', ticket_id=ticket.id))


@app.route('/tickets/<int:ticket_id>/comment', methods=['POST'])
@login_required
def ticket_comment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    content = request.form.get('content', '').strip()

    if not content:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    comment = Comment(
        ticket_id=ticket.id,
        user_id=current_user.id,
        content=content
    )
    db.session.add(comment)

    # Log activity
    log_activity(ticket.id, current_user.id, 'commented')
    ticket.updated_at = datetime.utcnow()
    db.session.commit()

    flash('Comment added.', 'success')
    return redirect(url_for('ticket_view', ticket_id=ticket.id))


@app.route('/tickets/<int:ticket_id>/attach', methods=['POST'])
@login_required
def ticket_attach(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit('.', 1)[1].lower()
        stored_filename = f'{uuid.uuid4().hex}.{ext}'

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], stored_filename))

        attachment = Attachment(
            ticket_id=ticket.id,
            filename=stored_filename,
            original_filename=original_filename,
            uploaded_by=current_user.id
        )
        db.session.add(attachment)

        # Log activity
        log_activity(ticket.id, current_user.id, 'attached', None, original_filename)
        ticket.updated_at = datetime.utcnow()
        db.session.commit()

        flash(f'File "{original_filename}" uploaded.', 'success')
    else:
        flash('File type not allowed.', 'danger')

    return redirect(url_for('ticket_view', ticket_id=ticket.id))


@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# -------------------- Audit Report --------------------

@app.route('/audit')
@login_required
def audit_log():
    # Filter by date range if provided
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    ticket_number = request.args.get('ticket_number', '')

    query = ActivityLog.query.join(Ticket)

    if ticket_number:
        query = query.filter(Ticket.ticket_number.ilike(f'%{ticket_number}%'))
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(ActivityLog.created_at >= start)
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(ActivityLog.created_at <= end)

    activities = query.order_by(ActivityLog.created_at.desc()).limit(500).all()
    return render_template('audit.html', activities=activities)


# -------------------- Template Filters --------------------

@app.template_filter('timeago')
def timeago_filter(dt):
    if not dt:
        return ''
    now = datetime.utcnow()
    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f'{mins}m ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours}h ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days}d ago'
    else:
        return dt.strftime('%Y-%m-%d')


@app.template_filter('status_badge')
def status_badge_filter(status):
    badges = {
        'open': 'bg-primary',
        'in_progress': 'bg-warning text-dark',
        'resolved': 'bg-success',
        'closed': 'bg-secondary'
    }
    return badges.get(status, 'bg-secondary')


@app.template_filter('priority_badge')
def priority_badge_filter(priority):
    badges = {
        'low': 'bg-info',
        'medium': 'bg-primary',
        'high': 'bg-warning text-dark',
        'critical': 'bg-danger'
    }
    return badges.get(priority, 'bg-secondary')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)
