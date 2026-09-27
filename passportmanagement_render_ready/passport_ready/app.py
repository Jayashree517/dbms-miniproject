from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

DATABASE = "passport.db"


# ---------------- DATABASE CONNECTION ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- CREATE TABLES ----------------

def create_tables():

    conn = get_db()
    cursor = conn.cursor()

    # Applicant table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applicants (
            applicant_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            dob TEXT,
            address TEXT
        )
    """)

    # Application table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            application_id INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id INTEGER NOT NULL,
            passport_type TEXT NOT NULL,
            application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Submitted',

            FOREIGN KEY (applicant_id)
            REFERENCES applicants(applicant_id)
        )
    """)

    # Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            document_number TEXT NOT NULL,
            verification_status TEXT DEFAULT 'Pending',

            FOREIGN KEY (application_id)
            REFERENCES applications(application_id)
        )
    """)

    # Admin table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Add one demo admin account
    cursor.execute("""
        INSERT OR IGNORE INTO admin (username, password)
        VALUES ('admin', 'admin123')
    """)

    conn.commit()
    conn.close()


# Create database tables when program starts
create_tables()


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]
        dob = request.form["dob"]
        address = request.form["address"]

        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO applicants
                (name, email, password, phone, dob, address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, email, password, phone, dob, address))

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered."

        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        applicant = conn.execute("""
            SELECT *
            FROM applicants
            WHERE email = ? AND password = ?
        """, (email, password)).fetchone()

        conn.close()

        if applicant:

            session["applicant_id"] = applicant["applicant_id"]
            session["name"] = applicant["name"]

            return redirect("/dashboard")

        return "Invalid email or password."

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "applicant_id" not in session:
        return redirect("/login")

    conn = get_db()

    applications = conn.execute("""
        SELECT *
        FROM applications
        WHERE applicant_id = ?
        ORDER BY application_date DESC
    """, (session["applicant_id"],)).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        applications=applications
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# ---------------- PASSPORT APPLICATION ----------------

@app.route("/apply", methods=["GET", "POST"])
def apply():

    if "applicant_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        passport_type = request.form["passport_type"]

        conn = get_db()

        conn.execute("""
            INSERT INTO applications
            (applicant_id, passport_type)
            VALUES (?, ?)
        """, (session["applicant_id"], passport_type))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("application.html")

# ---------------- DOCUMENTS ----------------

@app.route("/documents", methods=["GET", "POST"])
def documents():

    if "applicant_id" not in session:
        return redirect("/login")

    conn = get_db()

    # Get applications belonging to the logged-in applicant
    applications = conn.execute("""
        SELECT *
        FROM applications
        WHERE applicant_id = ?
        ORDER BY application_date DESC
    """, (session["applicant_id"],)).fetchall()

    # Add a new document
    if request.method == "POST":

        application_id = request.form["application_id"]
        document_type = request.form["document_type"]
        document_number = request.form["document_number"]

        # Make sure the application belongs to the logged-in applicant
        application = conn.execute("""
            SELECT *
            FROM applications
            WHERE application_id = ?
            AND applicant_id = ?
        """, (application_id, session["applicant_id"])).fetchone()

        if application:

            conn.execute("""
                INSERT INTO documents
                (application_id, document_type, document_number)
                VALUES (?, ?, ?)
            """, (
                application_id,
                document_type,
                document_number
            ))

            conn.commit()

        conn.close()

        return redirect("/documents")

    # Get existing documents
    documents = conn.execute("""
        SELECT
            documents.*,
            applications.passport_type
        FROM documents
        JOIN applications
        ON documents.application_id = applications.application_id
        WHERE applications.applicant_id = ?
        ORDER BY documents.document_id DESC
    """, (session["applicant_id"],)).fetchall()

    conn.close()

    return render_template(
        "documents.html",
        applications=applications,
        documents=documents
    )
# ---------------- ADMIN LOGIN ----------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        admin = conn.execute("""
            SELECT *
            FROM admin
            WHERE username = ? AND password = ?
        """, (username, password)).fetchone()

        conn.close()

        if admin:

            session["admin_id"] = admin["admin_id"]
            session["admin_username"] = admin["username"]

            return redirect("/admin/dashboard")

        return "Invalid admin username or password."

    return render_template("admin_login.html")

# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = get_db()

    # Get all applications with applicant details
    applications = conn.execute("""
        SELECT
            applications.*,
            applicants.name,
            applicants.email,
            applicants.phone
        FROM applications
        JOIN applicants
        ON applications.applicant_id = applicants.applicant_id
        ORDER BY applications.application_date DESC
    """).fetchall()


    # Count applications
    total_applications = conn.execute("""
        SELECT COUNT(*)
        FROM applications
    """).fetchone()[0]


    submitted = conn.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status = 'Submitted'
    """).fetchone()[0]


    approved = conn.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status = 'Approved'
    """).fetchone()[0]


    rejected = conn.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status = 'Rejected'
    """).fetchone()[0]


    conn.close()


    return render_template(
        "admin_dashboard.html",
        applications=applications,
        total_applications=total_applications,
        submitted=submitted,
        approved=approved,
        rejected=rejected
    )
# ---------------- MANAGE APPLICATION ----------------

@app.route("/admin/application/<int:application_id>",
           methods=["GET", "POST"])
def admin_application(application_id):

    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = get_db()


    if request.method == "POST":

        status = request.form["status"]

        conn.execute("""
            UPDATE applications
            SET status = ?
            WHERE application_id = ?
        """, (status, application_id))

        conn.commit()


    application = conn.execute("""
        SELECT
            applications.*,
            applicants.name,
            applicants.email,
            applicants.phone
        FROM applications
        JOIN applicants
        ON applications.applicant_id = applicants.applicant_id
        WHERE applications.application_id = ?
    """, (application_id,)).fetchone()


    conn.close()


    if application is None:
        return "Application not found."


    return render_template(
        "admin_application.html",
        application=application
    )
# ---------------- ADMIN LOGOUT ----------------

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_username", None)

    return redirect("/admin/login")
# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)