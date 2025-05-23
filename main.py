from flask import Flask,redirect, request, render_template, session, flash,url_for, jsonify#import the request object
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from datetime import datetime, timedelta
from collections import defaultdict
import json

app = Flask(__name__)#creats app
app.config['DEBUG'] = True#should keep app running while making changes
# Use SQLite instead of MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///get-it-done.db'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.secret_key = os.environ.get('SECRET_KEY', 'y337kGcys@zPB')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create all database tables
with app.app_context():
    db.create_all()

##ALL NECESSARY CODE TO RUN Web Application IN PYTHON
#CSS and JS must be in a static folder

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    category = db.Column(db.String(50), nullable=True)
    estimated_time = db.Column(db.Integer, nullable=True)  # in minutes
    actual_time = db.Column(db.Integer, default=0)  # in minutes
    timer_running = db.Column(db.Boolean, default=False)
    timer_start = db.Column(db.DateTime, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timer_started_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, name, owner, description="", due_date=None, priority="medium", category=None, estimated_time=None):
        self.name = name
        self.description = description
        self.completed = False
        self.owner = owner
        self.due_date = due_date
        self.priority = priority
        self.category = category
        self.estimated_time = estimated_time
        self.actual_time = 0
        self.timer_running = False
        self.timer_start = None
        self.timer_started_at = None

    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.timer_start = datetime.utcnow()

    def stop_timer(self):
        if self.timer_running:
            self.timer_running = False
            if self.timer_start:
                elapsed = datetime.utcnow() - self.timer_start
                self.actual_time += int(elapsed.total_seconds() / 60)
                self.timer_start = None

    def get_elapsed_time(self):
        if self.timer_running and self.timer_start:
            elapsed = datetime.utcnow() - self.timer_start
            return self.actual_time + int(elapsed.total_seconds() / 60)
        return self.actual_time

##end of class

#User Class
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    tasks = db.relationship('Task', backref='owner')
    
    def __init__(self, email, password):
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['POST', 'GET'])
@login_required
def index():
    if request.method == 'POST':
        task_name = request.form['task']   
        new_task = Task(task_name, current_user)
        db.session.add(new_task)
        db.session.commit()

    tasks = Task.query.filter_by(completed=False, owner=current_user).all()
    completed_tasks = Task.query.filter_by(completed=True, owner=current_user).all()
    
    # Calculate total time spent
    total_time_spent = sum(task.actual_time for task in tasks) + sum(task.actual_time for task in completed_tasks)
    
    # Calculate productivity score (example calculation)
    total_tasks = len(tasks) + len(completed_tasks)
    if total_tasks > 0:
        productivity_score = int((len(completed_tasks) / total_tasks) * 100)
    else:
        productivity_score = 0
    
    return render_template('todos.html', 
        title="Task Dashboard",
        tasks=tasks, 
        completed_tasks=completed_tasks,
        total_time_spent=total_time_spent,
        productivity_score=productivity_score
    )

@app.route('/delete-task', methods=['POST'])
@login_required
def delete_task():
    task_id = int(request.form['task-id'])
    task = Task.query.get(task_id)
    if task and task.owner == current_user:
        db.session.delete(task)
        db.session.commit()
    return redirect('/')

@app.route('/completed-task', methods=['POST'])
@login_required
def complete_task():
    task_id = int(request.form['task-id'])
    task = Task.query.get(task_id)
    if task and task.owner == current_user:
        task.completed = True
        db.session.add(task)
        db.session.commit()
    return redirect('/')

@app.route('/login', methods=['POST', 'GET'])  
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    user_count = User.query.count()
    flash(f'Current Subscribers: {user_count}')
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and user.password == password:
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])  
def register():  
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']
        
        if password != verify:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
            
        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('Registration successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email already registered.', 'danger')
            
    return render_template('register.html')    

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
@login_required
def add():
    task_name = request.form.get('task_name')
    description = request.form.get('description', '')
    due_date_str = request.form.get('due_date')
    priority = request.form.get('priority', 'medium')
    category = request.form.get('category')
    estimated_time = request.form.get('estimated_time')
    
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            pass
    
    # Ensure estimated_time is either an integer or None
    if estimated_time:
        try:
            estimated_time = int(estimated_time)
        except (ValueError, TypeError):
            estimated_time = None
    else:
        estimated_time = None
    
    if task_name:
        new_task = Task(
            name=task_name,
            owner=current_user,
            description=description,
            due_date=due_date,
            priority=priority,
            category=category,
            estimated_time=estimated_time
        )
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
@login_required
def complete(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner == current_user:
        task.completed = not task.completed
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
@login_required
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner == current_user:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/timer/<int:task_id>/start', methods=['GET'])
@login_required
def start_timer(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner != current_user:
        return jsonify({'error': 'Unauthorized'}), 403
    
    task.timer_started_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/timer/<int:task_id>/stop', methods=['GET'])
@login_required
def stop_timer(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner != current_user:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if task.timer_started_at:
        elapsed_time = (datetime.utcnow() - task.timer_started_at).total_seconds() / 60
        task.actual_time = (task.actual_time or 0) + elapsed_time
        task.timer_started_at = None
        db.session.commit()
    
    return jsonify({'success': True})

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner != current_user:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        task.name = request.form.get('task_name')
        task.description = request.form.get('description', '')
        due_date_str = request.form.get('due_date')
        task.priority = request.form.get('priority', 'medium')
        task.category = request.form.get('category')
        estimated_time = request.form.get('estimated_time')
        
        if due_date_str:
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                task.due_date = None
        
        # Ensure estimated_time is either an integer or None
        if estimated_time:
            try:
                task.estimated_time = int(estimated_time)
            except (ValueError, TypeError):
                task.estimated_time = None
        else:
            task.estimated_time = None
        
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('edit_task.html', task=task)

@app.route('/timer/<int:task_id>/status')
@login_required
def timer_status(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner != current_user:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'elapsed_time': task.get_elapsed_time(),
        'timer_running': task.timer_running
    })

@app.route('/dashboard')
@login_required
def dashboard():
    # Get active tasks
    active_tasks = Task.query.filter_by(completed=False, owner=current_user).all()
    
    # Get tasks completed today
    today = datetime.now().date()
    completed_today = Task.query.filter(
        Task.completed == True,
        Task.owner == current_user,
        Task.created_at >= today
    ).all()
    
    # Calculate total time spent today
    total_time_today = sum(task.actual_time or 0 for task in completed_today)
    
    # Get recent tasks (last 5)
    recent_tasks = Task.query.filter_by(owner=current_user)\
        .order_by(Task.created_at.desc())\
        .limit(5)\
        .all()
    
    return render_template('dashboard.html',
                         active_tasks=active_tasks,
                         completed_today=completed_today,
                         total_time_today=total_time_today,
                         recent_tasks=recent_tasks)

@app.route('/analytics')
@login_required
def analytics():
    # Get all tasks for the current user
    tasks = Task.query.filter_by(owner=current_user).all()
    completed_tasks = [task for task in tasks if task.completed]
    
    # Calculate basic stats
    total_tasks = len(tasks)
    total_time_spent = sum(task.actual_time or 0 for task in completed_tasks)
    avg_time_per_task = total_time_spent / len(completed_tasks) if completed_tasks else 0
    
    # Tasks by priority
    tasks_by_priority = {
        'high': len([t for t in tasks if t.priority == 'high']),
        'medium': len([t for t in tasks if t.priority == 'medium']),
        'low': len([t for t in tasks if t.priority == 'low'])
    }
    
    # Time spent by category
    category_times = defaultdict(int)
    for task in completed_tasks:
        if task.category:
            category_times[task.category] += task.actual_time or 0
    
    category_labels = list(category_times.keys())
    category_times = list(category_times.values())
    
    # Daily task completion for the last 7 days
    daily_completions = defaultdict(int)
    for task in completed_tasks:
        completion_date = task.created_at.date()
        if completion_date >= datetime.now().date() - timedelta(days=6):
            daily_completions[completion_date] += 1
    
    # Generate labels for the last 7 days
    daily_labels = [(datetime.now().date() - timedelta(days=i)).strftime('%Y-%m-%d')
                   for i in range(6, -1, -1)]
    daily_completions = [daily_completions.get(datetime.strptime(label, '%Y-%m-%d').date(), 0)
                        for label in daily_labels]
    
    # Calculate completion rate
    completion_rate = (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0
    
    return render_template('analytics.html',
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         total_time_spent=total_time_spent,
                         avg_time_per_task=round(avg_time_per_task, 1),
                         tasks_by_priority=tasks_by_priority,
                         category_labels=category_labels,
                         category_times=category_times,
                         daily_labels=daily_labels,
                         daily_completions=daily_completions,
                         completion_rate=round(completion_rate, 1))

@app.route('/task/<int:task_id>')
@login_required
def get_task_details(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner != current_user:
        abort(403)
    return jsonify({
        'id': task.id,
        'name': task.name,
        'description': task.description,
        'priority': task.priority,
        'category': task.category,
        'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
        'estimated_time': task.estimated_time,
        'actual_time': task.actual_time,
        'completed': task.completed
    })

if __name__ == '__main__':
    app.run()