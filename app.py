import os
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from models import db, User, Ticket, Comment, TicketHistory
from utils.priority import calculate_priority
from utils.sla import calculate_sla_deadline

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-later"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, 'database')
os.makedirs(DB_DIR, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(DB_DIR, 'helpdesk.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# ---------------- ACCESS CONTROL HELPERS ----------------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please login first.", "warning")
                return redirect(url_for('login'))
            if session.get('role') not in allowed_roles:
                flash("You are not authorized to access this page.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


def log_history(ticket_id, action):
    entry = TicketHistory(
        ticket_id=ticket_id,
        user_id=session['user_id'],
        action=action,
        created_at=datetime.utcnow()
    )
    db.session.add(entry)


# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return redirect(url_for('login'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        role = "employee"

        new_user = User(name=name, email=email, password_hash=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for('login'))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['name'] = user.name
            session['role'] = user.role
            flash("Login successful.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/admin-only")
@role_required('admin')
def admin_only_test():
    return "This page is visible ONLY to Admin."


@app.route("/create-ticket", methods=["GET", "POST"])
@login_required
def create_ticket():
    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        impact = request.form.get("impact", "")
        urgency = request.form.get("urgency", "")

        valid_categories = ['Hardware', 'Software', 'Network', 'Account/Login', 'Email', 'Access/Permissions', 'Application', 'Other']
        valid_levels = ['High', 'Medium', 'Low']

        if not subject or not description:
            flash("Subject and description cannot be empty.", "danger")
            return redirect(url_for('create_ticket'))

        if category not in valid_categories or impact not in valid_levels or urgency not in valid_levels:
            flash("Invalid category, impact, or urgency selected.", "danger")
            return redirect(url_for('create_ticket'))

        priority = calculate_priority(impact, urgency)
        created_at = datetime.utcnow()
        sla_deadline = calculate_sla_deadline(priority, created_at)

        last_ticket = Ticket.query.order_by(Ticket.id.desc()).first()
        next_id = (last_ticket.id + 1) if last_ticket else 1
        ticket_number = f"TCK-{next_id}"

        new_ticket = Ticket(
            ticket_number=ticket_number,
            user_id=session['user_id'],
            subject=subject,
            description=description,
            category=category,
            impact=impact,
            urgency=urgency,
            recommended_priority=priority,
            priority=priority,
            status="Open",
            created_at=created_at,
            sla_deadline=sla_deadline
        )

        db.session.add(new_ticket)
        db.session.flush()
        log_history(new_ticket.id, f"Ticket created with priority {priority}")
        db.session.commit()

        flash(f"Ticket {ticket_number} created successfully with priority {priority}.", "success")
        return redirect(url_for('dashboard'))

    return render_template("create_ticket.html")


@app.route("/my-tickets")
@login_required
def my_tickets():
    tickets = Ticket.query.filter_by(user_id=session['user_id']).order_by(Ticket.created_at.desc()).all()
    return render_template("my_tickets.html", tickets=tickets)


@app.route("/all-tickets")
@role_required('admin')
def all_tickets():
    ticket_number = request.args.get('ticket_number', '').strip()
    subject = request.args.get('subject', '').strip()
    category = request.args.get('category', '').strip()
    priority = request.args.get('priority', '').strip()
    status = request.args.get('status', '').strip()

    query = Ticket.query

    if ticket_number:
        query = query.filter(Ticket.ticket_number.ilike(f"%{ticket_number}%"))
    if subject:
        query = query.filter(Ticket.subject.ilike(f"%{subject}%"))
    if category:
        query = query.filter(Ticket.category == category)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if status:
        query = query.filter(Ticket.status == status)

    tickets = query.order_by(Ticket.created_at.desc()).all()
    agents = User.query.filter_by(role='agent').all()

    filters = {
        'ticket_number': ticket_number,
        'subject': subject,
        'category': category,
        'priority': priority,
        'status': status
    }

    return render_template("all_tickets.html", tickets=tickets, agents=agents, filters=filters)


@app.route("/admin-dashboard")
@role_required('admin')
def admin_dashboard():
    total_tickets = Ticket.query.count()
    open_tickets = Ticket.query.filter_by(status='Open').count()
    in_progress_tickets = Ticket.query.filter_by(status='In Progress').count()
    resolved_tickets = Ticket.query.filter(Ticket.status.in_(['Resolved', 'Closed'])).count()

    now = datetime.utcnow()
    sla_breached = Ticket.query.filter(
        Ticket.status.notin_(['Resolved', 'Closed']),
        Ticket.sla_deadline < now
    ).count()

    category_data = db.session.query(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).all()
    priority_data = db.session.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
    status_data = db.session.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()

    kpis = {
        'total': total_tickets,
        'open': open_tickets,
        'in_progress': in_progress_tickets,
        'resolved': resolved_tickets,
        'sla_breached': sla_breached
    }

    return render_template(
        "admin_dashboard.html",
        kpis=kpis,
        category_labels=[c[0] for c in category_data],
        category_values=[c[1] for c in category_data],
        priority_labels=[p[0] for p in priority_data],
        priority_values=[p[1] for p in priority_data],
        status_labels=[s[0] for s in status_data],
        status_values=[s[1] for s in status_data]
    )


@app.route("/assign-ticket/<int:ticket_id>", methods=["POST"])
@role_required('admin')
def assign_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    agent_id = request.form.get("agent_id")

    if not agent_id:
        flash("Please select an agent.", "warning")
        return redirect(url_for('all_tickets'))

    ticket.assigned_agent_id = agent_id
    ticket.assigned_at = datetime.utcnow()
    ticket.status = "Assigned"

    agent = User.query.get(agent_id)
    log_history(ticket.id, f"Assigned to {agent.name}")

    db.session.commit()
    flash(f"Ticket {ticket.ticket_number} assigned successfully.", "success")
    return redirect(url_for('all_tickets'))


@app.route("/agent-tickets")
@role_required('agent')
def agent_tickets():
    tickets = Ticket.query.filter_by(assigned_agent_id=session['user_id']).order_by(Ticket.created_at.desc()).all()
    return render_template("agent_tickets.html", tickets=tickets)


@app.route("/start-progress/<int:ticket_id>", methods=["POST"])
@role_required('agent')
def start_progress(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.assigned_agent_id != session['user_id']:
        flash("This ticket is not assigned to you.", "danger")
        return redirect(url_for('agent_tickets'))

    if ticket.status != 'Assigned':
        flash("Invalid status change.", "warning")
        return redirect(url_for('agent_tickets'))

    ticket.status = "In Progress"
    log_history(ticket.id, "Status changed to In Progress")
    db.session.commit()
    flash(f"Ticket {ticket.ticket_number} moved to In Progress.", "success")
    return redirect(url_for('agent_tickets'))


@app.route("/resolve-ticket/<int:ticket_id>", methods=["GET", "POST"])
@role_required('agent')
def resolve_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.assigned_agent_id != session['user_id']:
        flash("This ticket is not assigned to you.", "danger")
        return redirect(url_for('agent_tickets'))

    if ticket.status != 'In Progress':
        flash("Ticket must be In Progress before it can be resolved.", "warning")
        return redirect(url_for('agent_tickets'))

    if request.method == "POST":
        resolution_notes = request.form.get("resolution_notes")

        ticket.status = "Resolved"
        ticket.resolution_notes = resolution_notes
        ticket.resolved_at = datetime.utcnow()
        log_history(ticket.id, "Ticket resolved")
        db.session.commit()

        flash(f"Ticket {ticket.ticket_number} marked as Resolved.", "success")
        return redirect(url_for('agent_tickets'))

    return render_template("resolve_ticket.html", ticket=ticket)


@app.route("/knowledge-base")
@role_required('agent', 'admin')
def knowledge_base():
    query = request.args.get('q', '').strip()

    base_query = Ticket.query.filter(Ticket.status.in_(['Resolved', 'Closed']))

    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            db.or_(
                Ticket.subject.ilike(search_term),
                Ticket.description.ilike(search_term),
                Ticket.category.ilike(search_term),
                Ticket.resolution_notes.ilike(search_term)
            )
        )

    results = base_query.order_by(Ticket.resolved_at.desc()).all()
    return render_template("knowledge_base.html", results=results, query=query)


@app.route("/ticket/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def ticket_details(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    is_owner = ticket.user_id == session['user_id']
    is_assigned_agent = ticket.assigned_agent_id == session['user_id']
    is_admin = session['role'] == 'admin'

    if not (is_owner or is_assigned_agent or is_admin):
        flash("You are not authorized to view this ticket.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        comment_text = request.form.get("comment")
        new_comment = Comment(
            ticket_id=ticket.id,
            user_id=session['user_id'],
            comment=comment_text,
            created_at=datetime.utcnow()
        )
        db.session.add(new_comment)
        log_history(ticket.id, "Comment added")
        db.session.commit()
        flash("Comment added.", "success")
        return redirect(url_for('ticket_details', ticket_id=ticket.id))

    comments = Comment.query.filter_by(ticket_id=ticket.id).order_by(Comment.created_at.asc()).all()
    history = TicketHistory.query.filter_by(ticket_id=ticket.id).order_by(TicketHistory.created_at.asc()).all()

    return render_template("ticket_details.html", ticket=ticket, comments=comments, history=history)


@app.route("/reopen-ticket/<int:ticket_id>", methods=["POST"])
@login_required
def reopen_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.user_id != session['user_id']:
        flash("You can only reopen your own tickets.", "danger")
        return redirect(url_for('my_tickets'))

    if ticket.status != 'Resolved':
        flash("Only Resolved tickets can be reopened.", "warning")
        return redirect(url_for('my_tickets'))

    ticket.status = "Reopened"
    ticket.resolved_at = None
    log_history(ticket.id, "Ticket reopened by employee")
    db.session.commit()

    flash(f"Ticket {ticket.ticket_number} has been reopened.", "info")
    return redirect(url_for('my_tickets'))


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))


# ---------------- ERROR HANDLERS ----------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return render_template("500.html"), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)