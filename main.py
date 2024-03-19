from flask import Flask,redirect, request, render_template, session, flash,url_for#import the request object
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)#creats app
app.config['DEBUG'] = True#should keep app running while making changes
# Note: the connection string after :// contains the following info:
# user:password@server:portNumber/databaseName
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:admin@localhost:3306/get-it-done'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys@zPB'
##ALL NECESSARY CODE TO RUN Web Application IN PYTHON
#CSS and JS must be in a static folder

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    completed = db.Column(db.Boolean)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, name, owner):
        self.name = name
        self.completed = False
        self.owner = owner
##end of class

@app.route('/', methods=['POST', 'GET'])
def index():

    owner = User.query.filter_by(email=session['email']).first()

    if request.method == 'POST':
        task_name = request.form['task']   
        new_task = Task(task_name, owner)
        db.session.add(new_task)
        db.session.commit()

    tasks = Task.query.filter_by(completed=False,owner=owner).all()
    completed_tasks = Task.query.filter_by(completed=True,owner=owner).all()
    return render_template('todos.html', title="Get It Done!", 
        tasks=tasks, completed_tasks=completed_tasks)
#end of index
@app.route('/delete-task', methods=['POST'])
def delete_task():
    task_id = int(request.form['task-id'])#to get data from form
    task = Task.query.get(task_id)#to get data from database
    db.session.delete(task)
    db.session.commit()

    return redirect('/')
#end of delete    
@app.route('/completed-task', methods=['POST'])
def complete_task():
    task_id = int(request.form['task-id'])#to get data from form
    task = Task.query.get(task_id)#to get data from database
    task.completed=True
    db.session.add(task)
    db.session.commit()
    return redirect('/')
#end of completed list
#User Class
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(120),unique=True)#unique separates user experience
    password=db.Column(db.String(120))
    tasks = db.relationship('Task', backref='owner')
    def __init__(self, email,password):
        self.email = email
        self.password=password
#End of User Class

#login verification
@app.before_request#before all request run this function
def require_login():
    allowed_routes = ['login', 'register','static']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')


# login
@app.route('/login',methods=['POST', 'GET'])  
def login():  
    user_count = User.query.all()
    subscribers=len(user_count)
    print(f'There are {subscribers} subscrbers.')#how to post to html
    flash(f'Current Subscribers {subscribers}')#can I place this on page w/o flash
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        user=User.query.filter_by(email = email).first()
        if user and user.password == password:#info not separate
            session['email']=email
            flash('Logged in.','success')
            return redirect('/')
        else:
            flash('User password not correct or user does not exist.','danger')
                

    return render_template('login.html')
#end of login
# register    
@app.route('/register',methods=['POST', 'GET'])  
def register():  
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        verify=request.form['verify']#didn't require verify
        existing_user=User.query.filter_by(email=email).first()
        if not existing_user:
            new_user=User(email,password)
            db.session.add(new_user)
            db.session.commit()
            session['email']=email
            return redirect('/')
        else:
            return '<h1>Duplicate User</h1>'    
    return render_template('register.html')    
#end of register
#Logout
@app.route('/logout', methods=['GET'])
def logout():
    del session['email']
    return redirect('/')

if __name__ == '__main__':
    app.run()