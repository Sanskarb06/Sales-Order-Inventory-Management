from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    db.create_all()
    email = input("Admin email: ").strip()
    name = input("Admin name: ").strip()
    password = input("Admin password (use a strong password): ")
    if User.query.filter_by(email=email).first():
        print("That email already exists.")
    else:
        user = User(name=name, email=email, role="Admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("Admin account created. Sign in at /login.")
