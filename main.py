import json, re, smtplib, ssl
from flask import Flask, flash, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from decouple import config
from itsdangerous import URLSafeSerializer
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from magtifun_oop import MagtiFun

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
    phone=db.Column(db.String)
    preference=db.Column(db.String)
    email_confirmed=db.Column(db.Boolean, default=False)
    phone_confirmed = db.Column(db.Boolean, default=False)

    def __init__(self, name, email, address, district, preference, phone):
        self.name=name
        self.email=email
        self.address=address
        self.district=district
        self.preference=preference
        self.phone=phone


# function for confirming tokens
def confirm_token(token, salt: str):
    """Returns true if the token is valid and can be decrypted"""
    s = URLSafeSerializer(config('ITSDANGEROUS', default=""), salt=salt)
    try:
        id = s.loads(token)
    except:
        return False
    return id



def generate_token(id: str, salt: str):
    """Returns an encrypted token based off a user's ID"""
    s = URLSafeSerializer(config('ITSDANGEROUS', default=""), salt=salt)
    return s.dumps(id)

def generate_confirmation_email(user: User, token: str):
    """
    returns plaintext and html versions of
    a registration confirmation email
    based on the user's information"""
    plaintext = """\
Hi {name},

Thank you for signing up with Ar Aris.
Please confirm the below details are correct before confirming your registration:

Name: {name}
Address: {address}
District: {district}
Email address: {email}
Phone number: {phone}
Notification preference: {preference}

If any of the above is not correct, please reply to this email.
Otherwise, confirm your registration now:
https://www.araris.ge/confirmation/email/{token}

Cheers,

Ar Aris\
"""
    html = """\
<html>
    <body>
        <p>
            Hi {name},<br>
            <br>
            Thank you for signing up with Ar Aris.<br>
            Please confirm the below details are correct before confirming your registration:<br>
            <br>
            Name: <b>{name}</b><br>
            Address: <b>{address}</b><br>
            District: <b>{district}</b><br>
            Email address: <b>{email}</b><br>
            Phone number: <b>{phone}</b><br>
            Notification preference: <b>{preference}</b><br>
            <br>
            If any of the above is not correct, please reply to this email.<br>
            Otherwise, confirm your registration now:<br>
        </p>

        <table width="100%" cellspacing="0" cellpadding="0">
            <tr>
                <td>
                    <table cellspacing="0" cellpadding="0">
                        <tr>
                            <td style="border-radius: 2px;" bgcolor="#0000FF">
                                <a href="https://www.araris.ge/confirmation/email{token}" target="_blank" style="padding: 8px 12px; border: 1px solid #0000FF;border-radius: 2px;font-family: Helvetica, Arial, sans-serif;font-size: 14px; color: #ffffff;text-decoration: none;font-weight:bold;display: inline-block;">
                                    Confirm Registration           
                                </a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        <p>
        <br>
            Cheers,<br>
            <br>
            Ar Aris
        </p>
    </body>
</html>    
"""
    return (plaintext.format(name=user.name, 
                             address=user.address, 
                             district=user.district, 
                             email=user.email, phone=user.phone, 
                             preference=user.preference,
                             token=token),
            html.format(name=user.name, 
                        address=user.address, 
                        district=user.district, 
                        email=user.email, phone=user.phone, 
                        preference=user.preference,
                        token=token)
    )

def send_confirmation_email(user: User, token):
    """Sends an email to the newly-registered user.
    Includes all their info, so they can check the details are correct.
    Includes a link with a token to confirm their details and email address."""
    port = 465
    sender_email = config('EMAIL_USER', default='')
    sender_password = config('EMAIL_PW', default='')
    context = ssl.create_default_context()
    # Generate email message
    message = MIMEMultipart('alternative')
    message['subject'] = "Please confirm your registration to Ar Aris"
    message['from'] = sender_email
    message['to'] = user.email
    # Generate plaintext and html versions of the confirmation email
    plaintext, html = generate_confirmation_email(user, token)
    mime1 = MIMEText(plaintext, "plain")
    mime2 = MIMEText(html, "html")
    message.attach(mime1)
    message.attach(mime2)
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        # Login to the server
        server.login(sender_email, sender_password)
        # Send email
        server.sendmail(sender_email, user.email, message.as_string())
        # Cut server connection
        server.close()



def send_confirmation_text(user: User, token):
    """Texts the user to confirm their phone number"""
    template = """\
Hi {name},
Please click the following link to confirm you wish to receive utility disruption notifications via text:
https://www.araris.ge/confirmation/phone/{token}\
"""
    confirmation_text = template.format(name=user.name, token=token)
    m = MagtiFun(username=config('M_USER', default=''),
                 password=config('M_PW', default=''))
    
    if m.login():
        print("Authentication successful")

        m.get_balance()
        print("balance:", m.balance)

        if m.send_messages(user.phone, confirmation_text):
            print("All messages sent successfully")
        else:
            print("Some messages could not be sent. Check the log for more details")
            print(m.log_file)

    else:
        print("Authentication unsuccessful")



def confirm_registration(token, salt):
    """Changes the state of a user's phone/email notification confirmations"""
    id = confirm_token(token, salt)
    # If the ID is False, something was wrong with the token
    if not id:
        flash("The confirmation link is invalid", category="danger")
    # Otherwise, check if the user is in the DB
    else:
        user = db.session.execute(db.select(User).filter_by(id=id)).first()
    
        # If they are, change confirmed to True
        if user is not None:
            if salt == "Registration":
                if user[0].email_confirmed == False:
                    user[0].email_confirmed = True
                    flash(f"Email notifications confirmed", category="message")
                else:
                    flash(f"Email notifications already confirmed", category="danger")
            
            else:
                if user[0].phone_confirmed == False:
                    user[0].phone_confirmed = True
                    flash(f"Text notifications confirmed", category="message")
                else:
                    flash(f"Text notifications already confirmed", category="danger")
                
            db.session.commit()
            


@app.route("/confirmation/email/<token>", methods=["GET", "POST"])
def confirm_email(token):
    confirm_registration(token, "Registration")
    return render_template("index.html")



@app.route("/confirmation/phone/<token>", methods=["GET", "POST"])
def confirm_phone(token):
    confirm_registration(token, "Phone number")
    return render_template("index.html")



def validate_inputs(inputs: dict):
    """ Returns True inputs are not empty and are valid,
        otherwise returns False"""
    valid = True
        
    if inputs["name"] == "":
        # refresh page, flash warning?
        flash("Please enter your name", category="message")
        valid = False

    if inputs["email"] == "":
        flash("Please enter your email address", category="message")
        valid = False
    # A simple implementation to ensure email is in valid form (foo@bar.baz)
    # With email confirmation also, this is adequate
    elif not re.compile(r"[^@]+@[^@]+\.[^@]+").match(inputs["email"]):
        flash("Please enter a valid email address", category="message")
        valid = False

    # #  Disabled as district is obtained from Geojson matching
    # if inputs["district"] == "District":
    #     flash("Please select a district from the list", category="message")
    #     valid = False

    if inputs["address"] == "":
        flash("Please type an address and select it", category="message")
        valid = False

    if inputs["preference"] == "Notification preference":
        flash("Please select a notification preference")
        valid = False

    # Only require the phone number if the user wants text notifications
    if inputs["preference"] == "text" or inputs["preference"] == "both":
        if inputs["phone"] == "":
            flash("Please enter your mobile phone number")
            valid = False

        #Ensure phone number is valid form (e.g. starts with 59, 9 digits) 
        elif not re.compile(r"^(\+995)?\s?5\d{8}$").match(inputs["phone"]):
            flash("Please enter a valid Georgian mobile phone number", category="message")
            valid = False

    return valid



@app.route("/unsubscribe/<token>", methods=["GET", "POST"])
def unsubscribe_email(token):
    """Route for unsubscribing from email notifications"""
    id = confirm_token(token, "unsubscribe")
    # If ID is False, there's something wrong with the token
    if not id:
        flash("The unsubscription link is invalid", category="danger")
    
    # Otherwise, check if the user is still in the DB
    else:
        user = db.session.execute(db.select(User).filter_by(id=id)).first()
        # If they are, remove them
        if user is not None:
            db.session.delete(user[0])
            db.session.commit()
            flash("You have unsubscribed from all Ar Aris notifications", category="message")
        # Otherwise warn they've already been removed
        else:
            flash("You have already unsubscribed from Ar Aris", category="message")

    return render_template('index.html')



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")

    # If request method is post, submit the form to the DB
    else: 
        inputs = {
        "name": request.form.get("name"),
        "email": request.form.get("email"),
        "address": request.form.get("address"),
        "district": request.form.get("district"),
        "preference": request.form.get("preference"),
        "phone": request.form.get("phone"),
        }
        
        # Check input validity
        if validate_inputs(inputs) == False:
            # Inputs are invalid, so reload page and flash warnings
            return render_template("index.html")
        
        # ~~inputs are valid so:
        # Convert JSON back to dict format
        inputs["address"] = json.loads(inputs["address"])
        
        # Assign required values to variables
        # Some addresses don't have a ["street"] key, but instead have the name under
        # address["name_international"]["en"]
        if "name_international" in inputs["address"].keys():
            streetname = inputs["address"]["name_international"]["en"]
        else:
            streetname = inputs["address"]["street"]

        # Create user obj from info gained
        user=User(inputs["name"], inputs["email"], streetname, inputs["district"], inputs["preference"], inputs["phone"])

        # Ensure user has not already registered
        # Allow user to register muiltiple addresses per email
        # cross reference user email and address
        if db.session.execute(db.select(User).filter_by(address=streetname, email=inputs["email"])).all():
            flash("You've already registered this address", category="message")
            return render_template("index.html")

        # All is good, so add to db
        db.session.add(user)
        db.session.commit()
        # flash warning for user to confirm registration via email
        flash("Thanks for registering to Ar Aris", category="message")

        # Send the user a confirmation email
        email_token = generate_token(user.id, "Registration")
        send_confirmation_email(user, email_token)
        flash("Please check your emails to confirm your registration", category="message")

        # Send the user a confirmation text if they entered a number
        if inputs["phone"] is not None:
            phone_token = generate_token(user.id, "Phone number")
            send_confirmation_text(user, phone_token)
            flash("Please click the link we just texted you to receive text notifications", category="message")



        return redirect("/")



if __name__ == "__main__":
    app.run()
    # user=User("text", "sdf", "dfgfdggf st", "dicks", "both", "598865300")
    # # user = User( 'Shash', 'shashwighton@gmail.com', 'Ikalto street', 'Saburtalo', 'both', '598865300')
    # user.id = "2"
    # token = generate_token(user.id, "phone_confirmed")
    # print("token: ", token)
    # id = confirm_token(token, "phone_confirmed")
    # print("id: ", id)

    # send_confirmation_text(user, token)

