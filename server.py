from flask import Flask, render_template, redirect, request, session, flash
from flask_mysqldb import MySQL
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'nahid'
app.config['MYSQL_DB'] = 'bloodbank'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialize MySQL
mysql = MySQL(app)

# Create tables if not exists
def create_tables():
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS bloodbank;")
        cur.execute("USE bloodbank;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS donor (
              sno INT AUTO_INCREMENT PRIMARY KEY,
              username VARCHAR(255) NOT NULL,
              email VARCHAR(255),
              phno VARCHAR(15) NOT NULL,
              blood_group VARCHAR(5) NOT NULL,
              weight DECIMAL(5,2) NOT NULL,
              gender ENUM('Male', 'Female', 'Other') NOT NULL,
              dob DATE NOT NULL,
              address TEXT,
              password VARCHAR(255) NOT NULL,
              status TINYINT DEFAULT 1,
              last_donated DATE  
           );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('admin', 'user') NOT NULL DEFAULT 'user'
            );
        """)
        mysql.connection.commit()
        cur.close()

# Initialize table creation
create_tables()

@app.route("/")
def home():
    if 'username' in session:
        
        if session.get('role') == 'admin':
            return redirect("/admin/dashboard")
        else:
            return redirect("/user/dashboard")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')  # Use .get() to avoid KeyError if role is not present

        if role == 'admin':
            # Admin login
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
            user = cur.fetchone()
            cur.close()

            if user:
                session['username'] = username
                session['role'] = 'admin'
                return redirect("/admin/dashboard")
            else:
                flash("Invalid admin username or password")
        else:
            # Donor login
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM donor WHERE username=%s AND password=%s", (username, password))
            user = cur.fetchone()
            cur.close()

            if user:
                session['username'] = username
                session['role'] = 'user'  # Assuming 'user' role for donor
                return redirect("/user/dashboard")
            else:
                flash("Invalid donor username or password")
    
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phno = request.form['phno']
        blood_group = request.form['blood_group']
        weight = request.form['weight']
        gender = request.form['gender']
        dob = request.form['dob']
        address = request.form['address']
        
        # Donor registration
        cur = mysql.connection.cursor()
        cur.execute(""" 
            INSERT INTO donor (username, email, phno, blood_group, weight, gender, dob, address, password, last_donated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)  
        """, (username, email, phno, blood_group, weight, gender, dob, address, password))
        mysql.connection.commit()
        cur.close()
        flash("Donor registration successful")
        
        return redirect("/login")
    
    return render_template('register.html')

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'username' in session and session.get('role') == 'admin':
            return f(*args, **kwargs)
        else:
            flash("You need to be an admin to access this page")
            return redirect("/login")
    return wrap

def user_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'username' in session and session.get('role') == 'user':
            return f(*args, **kwargs)
        else:
            flash("You need to be a user to access this page")
            return redirect("/login")
    return wrap

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM donor WHERE status = 1")  # Fetch all active donors
    donors = cur.fetchall()
    cur.close()
    return render_template('admin_dashboard.html', tasks=donors)

@app.route("/user/dashboard")
@user_required
def user_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT *, DATEDIFF(CURRENT_DATE, last_donated) AS days_since_last_donation FROM donor WHERE status = 1")  # Fetch all active donors with last donated
    donors = cur.fetchall()
    cur.close()
    return render_template('user_dashboard.html', tasks=donors)

@app.route("/delete_donor/<int:sno>")
@admin_required
def delete_donor(sno):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM donor WHERE sno = %s", (sno,))
    mysql.connection.commit()
    cur.close()
    flash(f"Donor with serial number {sno} has been deleted", "success")
    return redirect("/admin/dashboard")
@app.route("/edit_donor/<int:sno>", methods=["GET", "POST"])
@admin_required
def edit_donor(sno):
    if request.method == "POST":
        # Retrieve form data
        email = request.form['email']
        phno = request.form['phno']
        blood_group = request.form['blood_group']
        weight = request.form['weight']
        gender = request.form['gender']
        address = request.form['address']
        last_donated = request.form['last_donated']  # Get last donated date from form

        # Update donor information in the database
        cur = mysql.connection.cursor()
        try:
            cur.execute(""" 
                UPDATE donor
                SET email = %s, phno = %s, blood_group = %s, weight = %s, gender = %s, address = %s, last_donated = %s
                WHERE sno = %s
            """, (email, phno, blood_group, weight, gender, address, last_donated, sno))
            mysql.connection.commit()
            flash(f"Donor with serial number {sno} has been updated", "success")
        except Exception as e:
            mysql.connection.rollback()  # Rollback on error
            flash(f"An error occurred: {str(e)}", "error")
        
        cur.close()
        return redirect("/admin/dashboard")
    
    # Fetch donor information for pre-populating the form
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM donor WHERE sno = %s", (sno,))
    donor = cur.fetchone()
    cur.close()

    return render_template('edit_donor.html', donor=donor)

@app.route("/user/profile", methods=["GET", "POST"])
@user_required
def user_profile():
    username = session['username']
    if request.method == "POST":
        # Retrieve form data
        email = request.form['email']
        phno = request.form['phno']
        blood_group = request.form['blood_group']
        weight = request.form['weight']
        gender = request.form['gender']
        address = request.form['address']
        last_donated = request.form['last_donated']  # Get last donated date from form

        # Update user information in the database
        cur = mysql.connection.cursor()
        cur.execute(""" 
            UPDATE donor
            SET email = %s, phno = %s, blood_group = %s, weight = %s, gender = %s, address = %s, last_donated = %s
            WHERE username = %s
        """, (email, phno, blood_group, weight, gender, address, last_donated, username))
        mysql.connection.commit()
        cur.close()

        flash("Your profile has been updated", "success")
        return redirect("/user/dashboard")

    # Fetch user information for pre-populating the form
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM donor WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()

    return render_template('user_profile.html', user=user)
@app.route("/update_admin")
def update_admin():
    # Check if admin is logged in
    if 'username' in session and session.get('role') == 'admin':
        username = session['username']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admin WHERE username = %s", (username,))
        admin = cur.fetchone()
        cur.close()

        if admin:
            return render_template('update_admin.html', admin=admin)
        else:
            flash("Admin not found", "error")
            return redirect("/admin/dashboard")  # Redirect to admin dashboard if admin not found

    flash("You need to be logged in as admin to access this page", "error")
    return redirect("/login")

@app.route("/update_admin_profile", methods=["POST"])
def update_admin_profile():
    if request.method == "POST":
        username = session['username']  # Retrieve admin username from session
        new_password = request.form['password']

        # Update admin password in the database
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE admin
            SET password = %s
            WHERE username = %s
        """, (new_password, username))
        mysql.connection.commit()
        cur.close()

        flash("Admin profile updated successfully", "success")
        return redirect("/admin/dashboard")  # Redirect to admin dashboard after update

    return redirect("/admin/dashboard")  # Redirect to dashboard if not a POST request

# Run the app if executed directly
if __name__ == "__main__":
    app.run(debug=True)
