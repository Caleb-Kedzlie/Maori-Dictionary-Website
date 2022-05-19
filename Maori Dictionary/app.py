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


def get_users():
    # Creates the connection to the database.
    con = create_connection(DB_NAME)

    # Gets the values from the categories table.
    query = "SELECT fname, lname, admin FROM users"
    cur = con.cursor()
    cur.execute(query)
    # Sets the fetched database variables into a table called user_table.
    user_table = cur.fetchall()
    con.close()
    # Returns the user table to other functions.
    return user_table


@app.route('/', methods=['GET', 'POST'])
def render_homepage():
    if request.method == 'POST':
        # Creates database connection and gets cursor for executing queries if user is modifying with "POST" method.
        con = create_connection(DB_NAME)
        cur = con.cursor()
        if request.form["button"] == "Add":
            category = request.form.get('insert_category').strip().capitalize()

            if len(category) < 4:
                return redirect('/?error=Categories+must+be+over+3+characters')

            # Creates the insert query to insert a category into the categories database.
            query = "INSERT INTO categories(id, category, link) VALUES(NULL,?,?)"

            # Gets the cursor to execute the query into the database except if there is a duplicate item.
            try:
                cur.execute(query, (category, category.replace(" / ", "&")))
            except sqlite3.IntegrityError:
                return redirect(f'/?error=Duplicate+item')

            # Commits the cursor execute through the database connection and then closes the connection.
            con.commit()
            con.close()
            print("Added category: {}".format(category))

        elif request.form["button"] == "Delete":
            category = request.form.get('remove_category').strip().capitalize()

            # Creates the delete query for the categories dictionary via an inputted category, then it's executed.
            query = "Delete from categories where link = ?"
            cur.execute(query, (category,))

            # Commits the cursor query and closes connection.
            con.commit()
            con.close()
            print("Removed category: {}".format(category))

    # Runs the main home page with all the variables inserted into the render template.
    return render_template('home.html', table=get_dictionary(), categories=get_categories(), users=get_users(),
                           logged_in=is_logged_in(), name=session.get('first_name'), admin=session.get('admin'))


@app.route('/main/<category>', methods=['GET', 'POST'])
def render_menu_page(category):
    if request.method == 'POST':
        print("Main post method")
        if request.form["button"] == "Delete":
            print("Trying to delete")
            # Creates the database connection and query.
            con = create_connection(DB_NAME)
            query = "Delete from dictionary where id = ?"
            # Selects dictionary and then deletes the id of the selected item.
            con.execute(query, (int(request.form["button"].replace("Delete ", "")),))
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
            print("Added item: {}".format(english))

    # Replaces '&' from the link with ' / ' to simplify modifying extracted table values in the html template script.
    current_category = category.replace("&", " / ").capitalize()
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

    return render_template('signup.html', categories=get_categories(), logged_in=is_logged_in(),
                           name=session.get('first_name'), admin=session.get('admin'))


@app.errorhandler(404)
def page_not_found(e):
    return redirect('base.html')


def is_logged_in():
    if session.get('email') is None:
        print("Currently not logged in")
        return False
    else:
        print("Currently logged in")
        return True


app.run(host='0.0.0.0')
