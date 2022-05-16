from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error

# from flask_bcrypt import bcrypt

DB_NAME = "C:/Users/18173/OneDrive - Wellington College/13DTS/Python/Maori Dictionary/dictionary.db"

app = Flask(__name__)
app.secret_key = "1qAZ2wSx3Edc4rfv5Tgb6yhn7ujM8Ik9ol0P"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        print(connection)
        return connection
    except Error as e:
        print(e)
    return None


def get_dictionary():
    # Creates the connection to the database.
    con = create_connection(DB_NAME)

    # Gets the values from the product table.
    query = "SELECT id, maori, english, category, definition, level FROM dictionary"

    # Executes the query to download from the database.
    cur = con.cursor()
    cur.execute(query)
    # Converts the values into a list to be sent through the site then closes the database.
    table = cur.fetchall()
    con.close()
    # Returns table from this function to the other scripts.
    return table


def get_categories():
    # Creates the connection to the database.
    con = create_connection(DB_NAME)

    # Gets the values from the categories table.
    query = "SELECT category, link FROM categories"
    # Gets the cursor and executes the query so the cursor can fetch all the values from the database then closes con.
    cur = con.cursor()
    cur.execute(query)
    categories_table = cur.fetchall()
    con.close()
    # Returns table from function to be used elsewhere.
    return categories_table


@app.route('/')
def render_homepage():
    # Runs the main home page with all the variables inserted into the render template.
    return render_template('home.html', table=get_dictionary(), categories=get_categories(),
                           logged_in=is_logged_in(), name=session.get('first_name'), admin=session.get('admin'))


@app.route('/main/<category>', methods=['GET', 'POST'])
def render_menu_page(category):
    if request.method == 'POST':
        print("Main post method")
        if "Delete" in request.form["button"]:
            print("Trying to delete")
            # Creates the database connection.
            con = create_connection(DB_NAME)
            # Selects dictionary and then deletes the id of the selected item.
            con.execute('Delete from dictionary where id = ?', [int(request.form["button"].replace("Delete ", ""))])
            con.commit()
            con.close()

            print('Deleted item #{}.'.format(request.form["button"].replace('Delete ', '')))
            return redirect(f'/main/{category}?Deleted+item')

        elif request.form["button"] == "AddItem":
            # Gets all the variables the user inputted into the row to add to the dictionary.
            maori = request.form.get('maori').strip().title()
            english = request.form.get('english').strip().title()
            definition = request.form.get('definition').strip().lower()
            level = request.form.get('level').strip()

            # Creates the database connection and the query.
            con = create_connection(DB_NAME)
            query = "INSERT INTO dictionary(id, maori, english, category, definition, level) VALUES(NULL,?,?,?,?,?)"

            # Executes the query to upload the words using the cursor then commits and closes the database.
            cur = con.cursor()
            try:
                cur.execute(query, (maori, english, category, definition, level))
            except sqlite3.IntegrityError:
                return redirect(f'/main/{category}?error=Duplicate+item')

            con.commit()
            con.close()
            print("Added item")

    # Replaces '&' from the link with ' / ' to simplify modifying extracted table values in the html template script.
    current_category = category.replace("&", " / ")
    print(current_category)

    return render_template("main.html", table=get_dictionary(), categories=get_categories(),
                           current=current_category, logged_in=is_logged_in(),
                           name=session.get('first_name'), admin=session.get('admin'))


@app.route('/logout')
def log_out():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect(request.referrer + '?message=See+you+soon')


@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        # Creates connection to database and extracts variables.
        con = create_connection(DB_NAME)
        query = "SELECT id, fname, password, admin FROM users WHERE email = ?"

        cursor = con.cursor()
        cursor.execute(query, (email,))
        user_data = cursor.fetchall()
        con.close()

        # Tries to get the user data from the login form and compare it with the table.
        try:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            db_password = user_data[0][2]
            is_admin = user_data[0][3]
            print(f"{user_id}, {first_name}, {db_password}, {password}")

            if db_password != password:
                return redirect(request.referrer + "?error=Password+incorrect")
        except IndexError:
            return redirect("/login?error=Email+or+password+invalid")

        # Encryption checking.
        # if not bcrypt.check_password_hash(db_password, password):
            # return redirect(request.referrer + "?error=password+encryption")

        # Sets the current session data to inform the website that the user is logged in.
        session['email'] = email
        session['user_id'] = user_id
        session['first_name'] = first_name
        session['admin'] = is_admin
        print("Setting email: " + session['email'])
        print(session)
        return redirect('/')

    # Gets all the categories and sends them through the render template to present all the category links.
    categories_list = get_categories(get_dictionary())

    return render_template('login.html', categories=get_categories(), logged_in=is_logged_in(),
                           name=session.get('first_name'), admin=session.get('admin'))


@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    if request.method == 'POST':
        # Gets all the variables the user inputted in the signup form.
        name = request.form.get('fname').strip().title()
        surname = request.form.get('lname').strip().title()
        email = request.form.get('email').strip().lower()
        password = request.form.get('pass').strip()
        password2 = request.form.get('pass2').strip()

        if len(password) < 8:
            return redirect('/signup?error=Passwords+must+be+8+characters+or+more')

        if password != password2:
            return redirect('/signup?error=Passwords+dont+match')

        # hashed_password = bcrypt.generate_password_hash(password)

        # Creates the database connection.
        con = create_connection(DB_NAME)

        # Creates the query.
        query = "INSERT INTO users(id, fname, lname, email, password) VALUES(NULL,?,?,?,?)"

        # Executes the query to upload to database then commits the change and closes database.
        cur = con.cursor()

        try:
            cur.execute(query, (name, surname, email, password))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+in+use')

        # Sets the current session data to inform the website that the user is logged in.
        session['email'] = email
        session['first_name'] = name

        con.commit()
        con.close()
        return redirect('/')

    # Gets all the categories and sends them through the render template to present all the category links.
    categories_list = get_categories(get_dictionary())

    return render_template('signup.html', categories=get_categories(), logged_in=is_logged_in(),
                           name=session.get('first_name'), admin=session.get('admin'))


def is_logged_in():
    if session.get('email') is None:
        print("Currently not logged in")
        return False
    else:
        print("Currently logged in")
        return True


app.run(host='0.0.0.0')
