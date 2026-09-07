from flask import Flask, render_template, request, redirect, session
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "civicclean-secret-key")

# =========================================
# DATABASE CONFIGURATION
# =========================================

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================================
# UPLOAD FOLDER
# =========================================

UPLOAD_FOLDER = "static/uploads/garbage"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================
# USER TABLE
# =========================================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), default="citizen")


# =========================================
# COMPLAINT TABLE
# =========================================

class Complaint(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)

    # Before cleanup photo
    image = db.Column(db.String(200))

    # After cleanup photo - uploaded by admin
    after_image = db.Column(db.String(200))

    description = db.Column(db.Text)

    garbage_type = db.Column(db.String(100))

    latitude = db.Column(db.Float)

    longitude = db.Column(db.Float)

    priority = db.Column(db.String(20), default="Medium")

    status = db.Column(db.String(30), default="Pending")


# =========================================
# HOME PAGE
# =========================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================
# REGISTER
# =========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already registered! Please use another email or login."

        # Hash password before storing it
        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return "Registration Successful! You can now login."

    return render_template("register.html")

# =========================================
# LOGIN
# =========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # Find user by email
        user = User.query.filter_by(email=email).first()

        # Verify hashed password
        if user and check_password_hash(user.password, password):

            # Save logged-in user's ID
            session["user_id"] = user.id

            # Save user's role
            session["role"] = user.role

            # Admin goes to Admin Dashboard
            if user.role == "admin":
                return redirect("/admin")

            # Citizen goes to Citizen Dashboard
            return redirect("/dashboard")

        return "Invalid Email or Password!"

    return render_template("login.html")

# =========================================
# LOGOUT
# =========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================
# CITIZEN DASHBOARD
# =========================================

# Citizen Dashboard
@app.route("/dashboard")
def dashboard():

    # Login check
    if "user_id" not in session:
        return redirect("/login")

    # Admin ko citizen dashboard par aane se rokna
    if session.get("role") == "admin":
        return redirect("/admin")

    # Logged-in user
    user = User.query.get(session["user_id"])

    # =========================================
    # ALL CITIZENS' COMPLAINTS
    # =========================================

    total = Complaint.query.count()

    pending = Complaint.query.filter_by(
        status="Pending"
    ).count()

    in_progress = Complaint.query.filter_by(
        status="In Progress"
    ).count()

    resolved = Complaint.query.filter_by(
        status="Resolved"
    ).count()


    # =========================================
    # LOGGED-IN CITIZEN'S COMPLAINTS
    # =========================================

    user_complaints = Complaint.query.filter_by(
        user_id=session["user_id"]
    ).all()


    return render_template(
        "dashboard.html",
        user=user,
        complaints=user_complaints,

        # All citizens statistics
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved
    )
    
    # Complaint counts
    total = Complaint.query.filter_by(
        user_id=session["user_id"]
    ).count()

    pending = Complaint.query.filter_by(
        user_id=session["user_id"],
        status="Pending"
    ).count()

    in_progress = Complaint.query.filter_by(
        user_id=session["user_id"],
        status="In Progress"
    ).count()

    resolved = Complaint.query.filter_by(
        user_id=session["user_id"],
        status="Resolved"
    ).count()

    return render_template(
        "dashboard.html",
        user=user,
        complaints=user_complaints,
        total=total,
        pending=pending,
        in_progress=in_progress,    
        resolved=resolved
    )
    

    # =====================================
    # GET ALL COMPLAINTS
    # =====================================

    all_complaints = Complaint.query.all()

    # =====================================
    # STATISTICS FOR ALL COMPLAINTS
    # =====================================

    total = Complaint.query.count()

    pending = Complaint.query.filter_by(
        status="Pending"
    ).count()

    in_progress = Complaint.query.filter_by(
        status="In Progress"
    ).count()

    resolved = Complaint.query.filter_by(
        status="Resolved"
    ).count()

    return render_template(
        "dashboard.html",

        # ALL complaints
        complaints=all_complaints,

        total=total,

        pending=pending,

        in_progress=in_progress,

        resolved=resolved
    )


# =========================================
# ADMIN DASHBOARD
# =========================================

@app.route("/admin")
def admin_dashboard():

    # Login check
    if "user_id" not in session:

        return redirect("/login")

    # Admin check
    if session.get("role") != "admin":

        return "Access Denied! Admins only.", 403

    # =====================================
    # ALL COMPLAINTS
    # =====================================

    all_complaints = Complaint.query.all()

    # =====================================
    # STATISTICS
    # =====================================

    total = Complaint.query.count()

    pending = Complaint.query.filter_by(
        status="Pending"
    ).count()

    in_progress = Complaint.query.filter_by(
        status="In Progress"
    ).count()

    resolved = Complaint.query.filter_by(
        status="Resolved"
    ).count()

    return render_template(
        "admin_dashboard.html",

        complaints=all_complaints,

        total=total,

        pending=pending,

        in_progress=in_progress,

        resolved=resolved
    )


# =========================================
# ADMIN UPDATE COMPLAINT STATUS
# =======================================

# =========================================
# ADMIN UPDATE COMPLAINT
# =========================================

# =========================================
# ADMIN UPDATE COMPLAINT
# =========================================

@app.route("/admin/update/<int:complaint_id>", methods=["GET", "POST"])
def update_complaint(complaint_id):

    # Check login
    if "user_id" not in session:
        return redirect("/login")

    # Check admin
    if session.get("role") != "admin":
        return "Access Denied! Admins only.", 403

    # Get complaint
    complaint = Complaint.query.get_or_404(complaint_id)

    if request.method == "POST":

        # Get selected status
        new_status = request.form["status"]

        # Get after cleanup image
        after_image = request.files.get("after_image")

        # =========================================
        # SAVE AFTER CLEANUP PHOTO
        # =========================================

        if after_image and after_image.filename:

            filename = secure_filename(after_image.filename)

            # Create unique filename
            filename = "after_" + str(complaint.id) + "_" + filename

            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            after_image.save(image_path)

            # Save filename in database
            complaint.after_image = filename

        # =========================================
        # UPDATE STATUS
        # =========================================

        complaint.status = new_status

        # Save changes
        db.session.commit()

        return redirect("/admin")

    return render_template(
        "update_complaint.html",
        complaint=complaint
    )

    # Check login
    if "user_id" not in session:
        return redirect("/login")

    # Check admin
    if session.get("role") != "admin":
        return "Access Denied! Admins only.", 403

    # Get complaint
    complaint = Complaint.query.get_or_404(complaint_id)

    if request.method == "POST":

        # Get selected status
        new_status = request.form["status"]

        # Get after-cleaning photo
        after_image = request.files.get("after_image")

        # =========================================
        # RESOLVED VALIDATION
        # =========================================

        if new_status == "Resolved":

            # Check if new photo is uploaded
            if not after_image or not after_image.filename:

                return """
                <script>
                    alert("Please upload the After Cleanup Photo before marking the complaint as Resolved.");
                    window.history.back();
                </script>
                """

            # Secure filename
            filename = secure_filename(after_image.filename)

            # Create unique filename
            filename = "after_" + str(complaint.id) + "_" + filename

            # Image path
            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            # Save image
            after_image.save(image_path)

            # Save filename in database
            complaint.after_image = filename

        # =========================================
        # OTHER STATUS
        # =========================================

        complaint.status = new_status

        # Save changes
        db.session.commit()

        return redirect("/admin")

    return render_template(
        "update_complaint.html",
        complaint=complaint
    )
    # Check login
    if "user_id" not in session:
        return redirect("/login")

    # Check admin
    if session.get("role") != "admin":
        return "Access Denied! Admins only.", 403

    # Get complaint
    complaint = Complaint.query.get_or_404(complaint_id)

    if request.method == "POST":

        # Get new status
        complaint.status = request.form["status"]

        # Get after-cleaning image
        after_image = request.files.get("after_image")

        # If admin uploaded a photo
        if after_image and after_image.filename:

            filename = secure_filename(after_image.filename)

            # Make filename unique
            filename = "after_" + str(complaint.id) + "_" + filename

            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            # Save image
            after_image.save(image_path)

            # Save filename in database
            complaint.after_image = filename

        # Save changes
        db.session.commit()

        return redirect("/admin")

    return render_template(
        "update_complaint.html",
        complaint=complaint
    )
def update_complaint(complaint_id):

    # Login check
    if "user_id" not in session:

        return redirect("/login")

    # Admin check
    if session.get("role") != "admin":

        return "Access Denied! Admins only.", 403

    complaint = Complaint.query.get_or_404(
        complaint_id
    )

    if request.method == "POST":

        complaint.status = request.form["status"]

        db.session.commit()

        return redirect("/admin")

    return render_template(
        "update_complaint.html",
        complaint=complaint
    )


# =========================================
# REPORT GARBAGE
# =========================================

@app.route("/report", methods=["GET", "POST"])
def report():

    # Login check
    if "user_id" not in session:

        return redirect("/login")

    if request.method == "POST":

        description = request.form["description"]

        garbage_type = request.form["garbage_type"]

        priority = request.form["priority"]

        latitude = request.form["latitude"]

        longitude = request.form["longitude"]

        image = request.files["image"]

        # Save image
        filename = secure_filename(
            image.filename
        )

        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        image.save(image_path)

        # =================================
        # CREATE COMPLAINT
        # =================================

        new_complaint = Complaint(

            user_id=session["user_id"],

            image=filename,

            description=description,

            garbage_type=garbage_type,

            latitude=float(latitude),

            longitude=float(longitude),

            priority=priority,

            status="Pending"
        )

        db.session.add(new_complaint)

        db.session.commit()

        return redirect("/complaints")

    return render_template("report.html")


# =========================================
# MY COMPLAINTS
# =========================================

@app.route("/complaints")
def complaints():

    # Login check
    if "user_id" not in session:

        return redirect("/login")

    # Currently showing only logged-in user's complaints
    user_complaints = Complaint.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "complaints.html",
        complaints=user_complaints
    )


# =========================================
# GARBAGE MAP
# =========================================

@app.route("/map")
def garbage_map():

    # Get ALL complaints
    complaints = Complaint.query.all()

    complaint_data = []

    for complaint in complaints:

        complaint_data.append({

            "id": complaint.id,

            "latitude": complaint.latitude,

            "longitude": complaint.longitude,

            "garbage_type": complaint.garbage_type,

            "description": complaint.description,

            "priority": complaint.priority,

            "status": complaint.status,

           "image": complaint.image,
           
           "after_image": complaint.after_image
        })

    return render_template(
        "map.html",
        complaints=complaint_data
    )


# =========================================
# CREATE DATABASE
# =========================================

with app.app_context():

    db.create_all()


# =========================================
# RUN APPLICATION
# =========================================

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)