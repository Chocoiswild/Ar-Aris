from flask import Flask, flash, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
import json
import re
from decouple import config

# Configure application
app = Flask(__name__)

# set secret key, keep this secret!
app.secret_key = config('APP_SECRET_KEY', default='')

# Ensure templates are auto-relaoded
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config['SQLALCHENY_TRACK_MODIFICATIONS'] = False


ENV = 'prod'

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:S92328102011@localhost/utility_scraper'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI']= config('DB_URL', default='')


db=SQLAlchemy(app)

class User(db.Model):
    __tablename__='users'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String)
    email=db.Column(db.String)
    address=db.Column(db.String)
    district=db.Column(db.String)

    def __init__(self, name, email, address, district):
        self.name=name
        self.email=email
        self.address=address
        self.district=district


@app.route("/", methods=["GET", "POST"])
def index():


    if request.method == "GET":
        return render_template("index.html")

    # If request method is post, submit the form to the DB
    else: 
        # Get the user's name, email, and address from the form
        name = request.form.get("name")
        email = request.form.get("email")
        address = request.form.get("address")
        district = request.form.get("district")

        # Ensure inputs are not empty
        if name == "":
            # refresh page, flash warning?
            flash("Please enter your name", category="message")
            return render_template("index.html")

        if email == "":
            flash("Please enter your email address", category="message")
            return render_template("index.html")

        if address == "":
            flash("Please type an address and select it", category="message")
            return render_template("index.html")
        if district == "District":
            flash("Please select a district from the list", category="message")
            return render_template("index.html")

        # A simple implementation to ensure email is in valid form (foo@bar.baz)
        # This needs to be changed later to email confirmation
        regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
        if not regex.match(email):
            flash("Please enter a valid email address", category="message")
            return render_template("index.html")
        
        # ~~inputs are valid so:
        # Convert JSON back to dict format
        address = json.loads(address)
        
        # Assign required values to variables
        # Some addresses don't have a ["street"] key, but instead have the name under
        # address["name_international"]["en"]
        if "name_international" in address.keys():
            streetname = address["name_international"]["en"]
        else:
            streetname = address["street"]

        
        # Create user obj from info gained
        user=User(name, email, streetname, district)

        # Ensure user has not already registered
        # Allow user to register muiltiple addresses per email
        # cross reference user email and address
        if db.session.execute(db.select(User).filter_by(address=streetname, email=email)).all():
            flash("You've already registered this address", category="message")
            return render_template("index.html")


        # All is good, so add to db
        db.session.add(user)
        db.session.commit()

        # flash warning that user saved to DB
        flash("Registered!", category="message")
        return redirect("/")


if __name__ == "__main__":
    app.run()
    # with app.app_context():
    #     db.create_all()
