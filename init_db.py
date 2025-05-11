from main import app, db, User, Task
from datetime import datetime

def init_db():
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create a test user
        test_user = User(email='test@example.com', password='password123')
        db.session.add(test_user)
        
        # Create a sample task
        sample_task = Task(
            name='Sample Task',
            description='This is a sample task',
            owner=test_user,
            due_date=datetime.utcnow(),
            priority='medium',
            category='Work',
            estimated_time=30
        )
        db.session.add(sample_task)
        
        # Commit the changes
        db.session.commit()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db() 