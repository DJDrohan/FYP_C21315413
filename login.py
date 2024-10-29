import hashlib
import os
import re
import psycopg2
import easygui as eg

# Database connection details
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "Sp00ky!"
DB_HOST = "localhost"
DB_PORT = "12345"

# Global variable to store the logged-in user
logged_in_user = None

# Function to hash passwords or answers using SHA-256 along with salt
def hash_data(data, salt):
    return hashlib.sha256((salt + data).encode()).hexdigest()

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

# Function to validate password complexity
def is_valid_password(password):
    if (len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)):
        return True
    else:
        eg.msgbox("Password must be at least 8 characters long, contain at least one uppercase letter, one number, and one special character.", "Invalid Password")
        return False

# Function to retrieve predefined security questions from the database
def get_security_questions():
    conn = connect_db()
    if not conn:
        return []

    questions = []
    with conn.cursor() as cur:
        cur.execute('SELECT question_id, question_text FROM "FaceUsers".security_questions')
        questions = cur.fetchall()  # List of tuples (question_id, question_text)
    conn.close()
    return questions

# Function to set a security question and answer for the user
def set_security_question(user_id):
    questions = get_security_questions()
    if not questions:
        eg.msgbox("No security questions available.", "Error")
        return

    # Display list of questions and let the user select one
    question_choices = [q[1] for q in questions]  # Extract only question_text for display
    question_text = eg.choicebox("Select a security question:", "Security Question", question_choices)
    if not question_text:
        eg.msgbox("No question selected. Please try again.", "Error")
        return

    # Find the selected question's ID
    selected_question_id = next(q[0] for q in questions if q[1] == question_text)

    answer = eg.passwordbox("Enter the answer to your selected security question:", "Security Answer")
    if not answer:
        eg.msgbox("No answer entered. Please try again.", "Error")
        return

    # Generate a random salt and hash the answer
    salt = os.urandom(16).hex()
    hashed_answer = hash_data(answer, salt)

    # Store the selected question ID, hashed answer, and salt in the security_answers table
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO "FaceUsers".security_answers (user_id, question_id, answer, salt) VALUES (%s, %s, %s, %s)',
                    (user_id, selected_question_id, hashed_answer, salt)
                )
                conn.commit()
            eg.msgbox("Security question saved successfully.", "Success")
        except psycopg2.IntegrityError:
            conn.rollback()
            eg.msgbox("A security question is already set for this user.", "Error")
        finally:
            conn.close()

# Function to check if a user already exists in the database
def check_user_exists(conn, username):
    with conn.cursor() as cur:
        cur.execute('SELECT 1 FROM "FaceUsers".users WHERE username = %s', (username,))
        return cur.fetchone() is not None

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
    if not password or not is_valid_password(password):
        return

    # Check if user already exists
    if check_user_exists(conn, username):
        eg.msgbox("Username already exists. Please try another one.", "Error")
        conn.close()
        return

    try:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO "FaceUsers".users (username) VALUES (%s) RETURNING id', (username,))
            user_id = cur.fetchone()[0]  # Get the newly created user's ID

            # Create a random salt and hash the password
            salt = os.urandom(16).hex()
            hashed_password = hash_data(password, salt)
            cur.execute(
                'INSERT INTO "FaceUsers".passwords (hashed_password, salt, user_id) VALUES (%s, %s, %s)',
                (hashed_password, salt, user_id)
            )
            conn.commit()

        # Set the security question and answer
        set_security_question(user_id)

        eg.msgbox("Sign-up successful! You can now log in.", "Success")

    except psycopg2.Error as e:
        conn.rollback()
        eg.msgbox(f"Error during sign-up: {e}", "Database Error")
    finally:
        conn.close()


# Function to verify user credentials
def verify_credentials(conn, username, password):
    with conn.cursor() as cur:
        cur.execute('''
            SELECT p.hashed_password, p.salt 
            FROM "FaceUsers".users u
            JOIN "FaceUsers".passwords p ON u.id = p.user_id
            WHERE u.username = %s
        ''', (username,))
        result = cur.fetchone()

        if result:
            stored_hashed_password, stored_salt = result
            hashed_password = hash_data(password, stored_salt)
            return hashed_password == stored_hashed_password
    return False

# Function to log in an existing user
def login():
    global logged_in_user
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

    if verify_credentials(conn, username, password):
        logged_in_user = username
        eg.msgbox("Login successful! Welcome.", "Success")
    else:
        eg.msgbox("Invalid username or password.", "Error")

    conn.close()

# Function to log out the user
def logout():
    global logged_in_user
    if logged_in_user:
        eg.msgbox(f"Goodbye, {logged_in_user}!", "Logout")
        logged_in_user = None  # Clear the in-memory session
    else:
        eg.msgbox("No user is currently logged in.", "Error")

def verify_security_question(user_id):
    conn = connect_db()
    if not conn:
        return False

    with conn.cursor() as cur:
        # Retrieve the security question, hashed answer, and salt for the user
        cur.execute('''
            SELECT q.question_text, a.answer, a.salt 
            FROM "FaceUsers".security_answers a
            JOIN "FaceUsers".security_questions q ON a.question_id = q.question_id
            WHERE a.user_id = %s
        ''', (user_id,))
        result = cur.fetchone()

        if result:
            question, stored_hashed_answer, stored_salt = result
            answer = eg.passwordbox(f"{question}:", "Security Question")

            # Hash the entered answer with the stored salt
            hashed_answer = hash_data(answer, stored_salt)

            # Compare stored hashed answer with the hashed version of the entered answer
            if hashed_answer == stored_hashed_answer:
                eg.msgbox("Security question verified successfully.", "Success")
                return True
            else:
                eg.msgbox("Incorrect answer to the security question.", "Error")

    conn.close()
    return False



# Function for password recovery
def recover_password():
    conn = connect_db()
    if not conn:
        return

    username = eg.enterbox("Enter your username for password recovery:", "Password Recovery")
    if not username:
        eg.msgbox("No username entered. Please try again.", "Error")
        return

    with conn.cursor() as cur:
        cur.execute('SELECT id FROM "FaceUsers".users WHERE username = %s', (username,))
        result = cur.fetchone()
        if not result:
            eg.msgbox("Username not found.", "Error")
            return

        user_id = result[0]

    # Verify the security question
    if not verify_security_question(user_id):
        return

    # Prompt user for a new password
    new_password = eg.passwordbox("Enter a new password:", "Reset Password")
    if not new_password or not is_valid_password(new_password):
        return

    # Hash the new password and update the database
    salt = os.urandom(16).hex()
    hashed_password = hash_data(new_password, salt)

    with conn.cursor() as cur:
        cur.execute('UPDATE "FaceUsers".passwords SET hashed_password = %s, salt = %s WHERE user_id = %s',
                    (hashed_password, salt, user_id))
        conn.commit()

    conn.close()
    eg.msgbox("Password reset successfully. You can now log in with your new password.", "Success")

# Main menu for sign-up, login, logout, and password recovery
def main():
    while True:
        if logged_in_user:
            choice = eg.buttonbox(f"Welcome, {logged_in_user}! Please choose an option:",
                                  "Main Menu", ["Logout", "Exit"])
        else:
            choice = eg.buttonbox("Welcome! Please choose an option:", "Main Menu",
                                  ["Sign Up", "Login", "Recover Password", "Exit"])

        if choice == "Sign Up":
            sign_up()
        elif choice == "Login":
            login()
        elif choice == "Logout":
            logout()
        elif choice == "Recover Password":
            recover_password()
        elif choice == "Exit":
            eg.msgbox("Goodbye!", "Exit")
            break
        else:
            eg.msgbox("Invalid choice. Please try again.", "Error")

if __name__ == "__main__":
    main()
