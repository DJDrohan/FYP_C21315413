import hashlib
import os
import psycopg2
import easygui as eg  # Import EasyGUI for GUI dialogs

# Database connection details
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "Sp00ky!"
DB_HOST = "localhost"
DB_PORT = "12345"

# Global variable to store the logged-in user "Session token"
logged_in_user = None

# Function to check if a user is logged in before performing any action
def check_logged_in():
    if logged_in_user is None:
        eg.msgbox("You need to log in first!", "Error")
        return False
    return True

# Function to log out the user
def logout():
    global logged_in_user  # Declare global to modify it
    if logged_in_user:
        eg.msgbox(f"Goodbye, {logged_in_user}!", "Logout")
        logged_in_user = None  # Clear the in-memory session
    else:
        eg.msgbox("No user is currently logged in.", "Error")



# Function to hash passwords using SHA-256 along with salt
def hash_password(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()

# Function to connect to the PostgreSQL database
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        eg.msgbox(f"Error connecting to the database: {e}", "Database Error")
        return None

# Function to sign up a new user
def sign_up():
    conn = connect_db()
    if not conn:
        return

    username = eg.enterbox("Enter a username:", "Sign Up")
    if not username:
        eg.msgbox("No username entered. Please try again.", "Error")
        return

    password = eg.passwordbox("Enter a password:", "Sign Up")
    if not password:
        eg.msgbox("No password entered. Please try again.", "Error")
        return

    # Check if user already exists
    if check_user_exists(conn, username):
        eg.msgbox("Username already exists. Please try another one.", "Error")
        return

    # Create a new user in the FaceUsers.users table
    with conn.cursor() as cur:
        cur.execute('INSERT INTO "FaceUsers".users (username) VALUES (%s) RETURNING id', (username,))
        user_id = cur.fetchone()[0]  # Get the newly created user's ID

        # Create a random salt
        salt = os.urandom(16).hex()

        # Hash the password with the salt
        hashed_password = hash_password(password, salt)

        # Store the hashed password, salt, and user_id in the FaceUsers.passwords table
        cur.execute(
            'INSERT INTO "FaceUsers".passwords (hashed_password, salt, user_id) VALUES (%s, %s, %s)',
            (hashed_password, salt, user_id)
        )
        conn.commit()

    eg.msgbox("Sign-up successful! You can now log in.", "Success")
    conn.close()

# Function to log in an existing user
def login():
    global logged_in_user #"session token"
    conn = connect_db()
    if not conn:
        return

    username = eg.enterbox("Enter your username:", "Login")
    if not username:
        eg.msgbox("No username entered. Please try again.", "Error")
        return

    password = eg.passwordbox("Enter your password:", "Login")
    if not password:
        eg.msgbox("No password entered. Please try again.", "Error")
        return

    # Verify if the user exists and the password matches
    if verify_credentials(conn, username, password):
        logged_in_user = username
        eg.msgbox("Login successful! Welcome.", "Success")
    else:
        eg.msgbox("Invalid username or password.", "Error")

    conn.close()

# Function to check if a user already exists in the database
def check_user_exists(conn, username):
    with conn.cursor() as cur:
        # Query to check if the username exists in the FaceUsers.users table
        cur.execute('SELECT 1 FROM "FaceUsers".users WHERE username = %s', (username,))
        return cur.fetchone() is not None



# Function to verify user credentials
def verify_credentials(conn, username, password):
    with conn.cursor() as cur:
        # Query to get the hashed password and salt for the user from the FaceUsers.passwords table
        cur.execute('''
            SELECT p.hashed_password, p.salt 
            FROM "FaceUsers".users u
            JOIN "FaceUsers".passwords p ON u.id = p.user_id
            WHERE u.username = %s
        ''', (username,))
        result = cur.fetchone()

        if result:
            stored_hashed_password, stored_salt = result
            hashed_password = hash_password(password, stored_salt)

            # Compare stored hashed password with the hashed version of the entered password
            if hashed_password == stored_hashed_password:
                return True

    return False

# Main menu for sign-up or login
def main():
    while True:
        if logged_in_user:
            # If the user is logged in, show a welcome message and allow logout
                choice = eg.buttonbox(f"Welcome, {logged_in_user}! Please choose an option:",
                                          "Main Menu", ["Logout", "Exit"])
        else:
            # If no user is logged in, offer Sign Up and Login options
            choice = eg.buttonbox("Welcome! Please choose an option:", "Main Menu",
                                ["Sign Up", "Login", "Exit"])

        if choice == "Sign Up":
            sign_up()
        elif choice == "Login":
            login()
        elif choice == "Logout":
            logout()
        elif choice == "Exit":
            eg.msgbox("Goodbye!", "Exit")
            break
        else:
            eg.msgbox("Invalid choice. Please try again.", "Error")


if __name__ == "__main__":
    main()
