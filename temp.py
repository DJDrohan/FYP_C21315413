import tkinter as tk
from tkinter import messagebox, simpledialog
import hashlib
import os
import re
import psycopg2
import easygui as eg

# Import the access_camera function from camerainput.py
from camerainput import access_camera

# Create the main application window
root = tk.Tk()
root.title("User Login System")
root.geometry("400x300")

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
        messagebox.showerror("Database Error", f"Error connecting to the database: {e}")
        return None

# Function to validate password complexity
def is_valid_password(password):
    if (len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)):
        return True
    else:

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


# Signup function using Tkinter dialogs with password confirmation
def sign_up():
    conn = connect_db()
    if not conn:
        return

    username = simpledialog.askstring("Sign Up", "Enter a username:")
    if not username:
        messagebox.showwarning("Error", "No username entered. Please try again.")
        return

    # Function to get and confirm password input
    def get_confirmed_password():
        pw_window = tk.Toplevel(root)
        pw_window.title("Set Password")
        tk.Label(pw_window, text="Enter password:").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(pw_window, text="Confirm password:").grid(row=1, column=0, padx=5, pady=5)

        entry_password = tk.Entry(pw_window, show="*")
        entry_confirm_password = tk.Entry(pw_window, show="*")
        entry_password.grid(row=0, column=1, padx=5, pady=5)
        entry_confirm_password.grid(row=1, column=1, padx=5, pady=5)

        # Inner function to validate passwords and close window if valid
        def submit_password():
            password = entry_password.get()
            confirm_password = entry_confirm_password.get()

            if not password:
                messagebox.showwarning("Error", "Password cannot be empty.")
            elif password != confirm_password:
                messagebox.showwarning("Error", "Passwords do not match.")
            elif not is_valid_password(password):
                messagebox.showwarning("Invalid Password",
                                       "Password must be at least 8 characters long, "
                                       "contain at least one uppercase letter, one number, "
                                       "and one special character.")
            else:
                pw_window.destroy()
                complete_signup(username, password)  # Continue with signup if passwords are valid

        tk.Button(pw_window, text="Submit", command=submit_password).grid(row=2, columnspan=2, pady=10)
        pw_window.transient(root)
        pw_window.grab_set()
        root.wait_window(pw_window)

    # Function to complete signup after successful password confirmation
    def complete_signup(username, password):
        try:
            with conn.cursor() as cur:
                # Check if user already exists
                if check_user_exists(conn, username):
                    messagebox.showwarning("Error", "Username already exists. Please try another one.")
                    return

                # Insert the user into the users table
                cur.execute('INSERT INTO "FaceUsers".users (username) VALUES (%s) RETURNING id', (username,))
                user_id = cur.fetchone()[0]

                # Hash the confirmed password
                salt = os.urandom(16).hex()
                hashed_password = hash_data(password, salt)
                cur.execute(
                    'INSERT INTO "FaceUsers".passwords (hashed_password, salt, user_id) VALUES (%s, %s, %s)',
                    (hashed_password, salt, user_id)
                )
                conn.commit()

            # Set the security question and answer (keeping EasyGUI for the selection part)
            set_security_question(user_id)
            messagebox.showinfo("Success", "Sign-up successful! You can now log in.")

        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror("Database Error", f"Error during sign-up: {e}")
        finally:
            conn.close()

    # Call password confirmation function
    get_confirmed_password()


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

# Login function using Tkinter dialogs
def login():
    global logged_in_user
    conn = connect_db()
    if not conn:
        return

    username = simpledialog.askstring("Login", "Enter your username:")
    if not username:
        messagebox.showwarning("Error", "No username entered. Please try again.")
        return

    password = simpledialog.askstring("Login", "Enter your password:", show="*")
    if not password:
        messagebox.showwarning("Error", "No password entered. Please try again.")
        return

    # Authenticate user credentials
    with conn.cursor() as cur:
        cur.execute('SELECT id FROM "FaceUsers".users WHERE username = %s', (username,))
        result = cur.fetchone()

        if result:
            user_id = result[0]
            logged_in_user = username
            messagebox.showinfo("Success", "Login successful! Welcome.")

            # Insert into sessions table to mark the user as logged in
            try:
                cur.execute('INSERT INTO "FaceUsers".sessions (user_id) VALUES (%s)', (user_id,))
                conn.commit()
            except psycopg2.IntegrityError:
                conn.rollback()
                messagebox.showwarning("Session Active", "You are already logged in on another device or session.")
        else:
            messagebox.showerror("Error", "Invalid username or password.")

    conn.close()


# Logout function
def logout():
    global logged_in_user
    conn = connect_db()
    if not conn:
        return

    if logged_in_user:
        messagebox.showinfo("Logout", f"Goodbye, {logged_in_user}!")

        # Remove from sessions table to mark user as logged out
        with conn.cursor() as cur:
            cur.execute(
                'DELETE FROM "FaceUsers".sessions WHERE user_id = (SELECT id FROM "FaceUsers".users WHERE username = %s)',
                (logged_in_user,))
            conn.commit()

        logged_in_user = None  # Clear the in-memory session
    else:
        messagebox.showwarning("Warning", "No user is currently logged in.")

    conn.close()

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


def recover_password():
    conn = connect_db()
    if not conn:
        return

    # Step 1: Prompt for Username
    username = simpledialog.askstring("Password Recovery", "Enter your username:")
    if not username:
        messagebox.showwarning("Error", "No username entered. Please try again.")
        return

    # Step 2: Check if the user exists
    with conn.cursor() as cur:
        cur.execute('SELECT id FROM "FaceUsers".users WHERE username = %s', (username,))
        result = cur.fetchone()
        if not result:
            messagebox.showerror("Error", "Username not found.")
            return
        user_id = result[0]

    # Step 3: Verify Security Question
    if not verify_security_question(user_id):
        messagebox.showerror("Security Verification Failed", "Incorrect answer to the security question.")
        return

    # Step 4: Get a Valid New Password (with confirmation)
    def get_new_password():
        # Nested function to create a password confirmation window
        pw_window = tk.Toplevel(root)
        pw_window.title("Reset Password")
        tk.Label(pw_window, text="Enter new password:").grid(row=0, column=0)
        tk.Label(pw_window, text="Confirm new password:").grid(row=1, column=0)

        # Password entry fields
        entry_password = tk.Entry(pw_window, show="*")
        entry_confirm_password = tk.Entry(pw_window, show="*")
        entry_password.grid(row=0, column=1)
        entry_confirm_password.grid(row=1, column=1)

        # Function to validate and capture the password input
        def submit_password():
            password = entry_password.get()
            confirm_password = entry_confirm_password.get()

            if not password:
                messagebox.showwarning("Error", "Password cannot be empty.")
            elif password != confirm_password:
                messagebox.showwarning("Error", "Passwords do not match.")
            elif not is_valid_password(password):
                messagebox.showwarning("Invalid Password",
                                       "Password must be at least 8 characters long, "
                                       "contain at least one uppercase letter, one number, "
                                       "and one special character.")
            else:
                pw_window.destroy()
                update_password(password)  # Update the password if valid and confirmed

        tk.Button(pw_window, text="Submit", command=submit_password).grid(row=2, columnspan=2, pady=10)
        pw_window.transient(root)
        pw_window.grab_set()
        root.wait_window(pw_window)

    def update_password(new_password):
        # Step 5: Hash and Save the New Password
        salt = os.urandom(16).hex()
        hashed_password = hash_data(new_password, salt)

        with conn.cursor() as cur:
            cur.execute('UPDATE "FaceUsers".passwords SET hashed_password = %s, salt = %s WHERE user_id = %s',
                        (hashed_password, salt, user_id))
            conn.commit()

        messagebox.showinfo("Success", "Password reset successfully. You can now log in with your new password.")

    # Call get_new_password to prompt the user for new password and confirmation
    get_new_password()
    conn.close()


# Main menu for sign-up, login, logout, and password recovery
def main():
    while True:
        if logged_in_user:
            choice = eg.buttonbox(f"Welcome, {logged_in_user}! Please choose an option:",
                                  "Main Menu", ["Access Camera", "Logout", "Exit"])
        else:
            choice = eg.buttonbox("Welcome! Please choose an option:", "Main Menu",
                                  ["Sign Up", "Login", "Recover Password", "Exit"])

        if choice == "Sign Up":
            sign_up()
        elif choice == "Login":
            login()
        elif choice == "Recover Password":
            recover_password()
        elif choice == "Logout":
            logout()
        elif choice == "Access Camera":
            access_camera()
        elif choice == "Exit":
            if logged_in_user:
                logout()  # Clear session before exiting
            eg.msgbox("Goodbye!", "Exit")
            break
        else:
            eg.msgbox("Invalid choice. Please try again.", "Error")

if __name__ == "__main__":
    main()