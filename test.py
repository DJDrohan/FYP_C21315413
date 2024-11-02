import tkinter as tk
from tkinter import messagebox, simpledialog
import hashlib
import os
import re
import psycopg2
from camerainput import access_camera  # Import camera function

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
        messagebox.showwarning("Invalid Password",
                               "Password must be at least 8 characters long, contain at least one uppercase letter, one number, and one special character.")
        return False

# Signup function using Tkinter dialogs
def sign_up():
    conn = connect_db()
    if not conn:
        return

    username = simpledialog.askstring("Sign Up", "Enter a username:")
    if not username:
        messagebox.showwarning("Error", "No username entered. Please try again.")
        return

    password = simpledialog.askstring("Sign Up", "Enter a password:", show="*")
    if not password or not is_valid_password(password):
        return

    # Check if user already exists
    if check_user_exists(conn, username):
        messagebox.showwarning("Error", "Username already exists. Please try another one.")
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

        # Set the security question and answer (keeping EasyGUI for the selection part)
        set_security_question(user_id)

        messagebox.showinfo("Success", "Sign-up successful! You can now log in.")

    except psycopg2.Error as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"Error during sign-up: {e}")
    finally:
        conn.close()

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

# Function to reset password with Tkinter dialogs
def recover_password():
    conn = connect_db()
    if not conn:
        return

    username = simpledialog.askstring("Password Recovery", "Enter your username:")
    if not username:
        messagebox.showwarning("Error", "No username entered. Please try again.")
        return

    with conn.cursor() as cur:
        cur.execute('SELECT id FROM "FaceUsers".users WHERE username = %s', (username,))
        result = cur.fetchone()
        if not result:
            messagebox.showerror("Error", "Username not found.")
            return

        user_id = result[0]

    # Verify the security question using EasyGUI for the prompt
    if not verify_security_question(user_id):
        return

    # Prompt user for a new password
    new_password = simpledialog.askstring("Reset Password", "Enter a new password:", show="*")
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
    messagebox.showinfo("Success", "Password reset successfully. You can now log in with your new password.")

# Tkinter buttons for GUI
btn_login = tk.Button(root, text="Login", command=login)
btn_login.pack(pady=5)

btn_logout = tk.Button(root, text="Logout", command=logout)
btn_logout.pack(pady=5)

btn_signup = tk.Button(root, text="Sign Up", command=sign_up)
btn_signup.pack(pady=5)

btn_recover_password = tk.Button(root, text="Recover Password", command=recover_password)
btn_recover_password.pack(pady=5)

btn_camera = tk.Button(root, text="Access Camera", command=access_camera)
btn_camera.pack(pady=5)

# Run the Tkinter main loop
root.mainloop()
