import mysql.connector
import getpass  # For securely typing passwords
import datetime

# --- DATABASE CONFIGURATION ---
# !! Update these values with your MySQL credentials !!
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # <-- IMPORTANT: Change this
    'database': 'pesuconnect'
}
# ------------------------------


def connect_to_db():
    """Establishes a connection to the database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

def student_login(conn):
    """Handles the student login process."""
    print("--- PESUConnect Login ---")
    email = input("Email (@pesu.edu): ")
    password = getpass.getpass("Password (hidden): ") # Hides password as you type

    try:
        cursor = conn.cursor(dictionary=True)
        # Call the sp_StudentLogin procedure
        cursor.callproc('sp_StudentLogin', [email, password])
        
        user = None
        # Stored procedure results are returned as iterators
        for result in cursor.stored_results():
            user = result.fetchone()
            
        cursor.close()
        
        if user:
            print(f"\nLogin successful! Welcome, {user['name']}.")
            return user  # Returns the user's data (student_id, name, email)
        else:
            print("\nLogin failed: Invalid credentials.")
            return None
            
    except mysql.connector.Error as err:
        print(f"Login error: {err}")
        return None

def view_projects(conn):
    """Fetches and displays all 'Open' projects."""
    print("\n--- Available Projects ---")
    try:
        cursor = conn.cursor(dictionary=True)
        # Call sp_SearchProjects, keyword=NULL, status='Open'
        cursor.callproc('sp_SearchProjects', [None, 'Open'])

        projects = []
        for result in cursor.stored_results():
            projects = result.fetchall()
            
        cursor.close()

        if not projects:
            print("No open projects found.")
            return

        for proj in projects:
            # Format the deadline for nice printing
            deadline_date = proj['deadline'].strftime('%Y-%m-%d')
            print("-------------------------")
            print(f"  ID: {proj['project_id']}")
            print(f"  Title: {proj['title']}")
            print(f"  Owner: {proj['owner_name']}")
            print(f"  Deadline: {deadline_date}")
            print(f"  Description: {proj['description']}")
        print("-------------------------")
            
    except mysql.connector.Error as err:
        print(f"Error fetching projects: {err}")

def create_project(conn, user_id):
    """Walks the user through creating a new project."""
    print("\n--- Create a New Project ---")
    try:
        title = input("Project Title: ")
        description = input("Project Description: ")
        
        # Get and validate the deadline date
        while True:
            deadline_str = input("Deadline (YYYY-MM-DD): ")
            try:
                deadline = datetime.datetime.strptime(deadline_str, '%Y-%m-%d').date()
                if deadline <= datetime.date.today():
                    print("Error: Deadline must be in the future.")
                else:
                    break # Date is valid and in the future
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD.")
        
        cursor = conn.cursor()
        # Call your updated sp_CreateProject
        cursor.callproc('sp_CreateProject', [user_id, title, description, deadline])
        
        # Commit the transaction to save the new project
        conn.commit()
        
        print("\nSuccess! Your project has been posted.")
        cursor.close()

    except mysql.connector.Error as err:
        print(f"Error creating project: {err}")
        conn.rollback() # Rollback changes if an error occurred

def show_dashboard(conn, user):
    """Main menu for a logged-in user."""
    while True:
        print("\n--- Dashboard ---")
        print(f"Logged in as: {user['name']}")
        print("1. View Available Projects")
        print("2. Create a New Project")
        print("3. Logout")
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            view_projects(conn)
        elif choice == '2':
            create_project(conn, user['student_id'])
        elif choice == '3':
            print("\nLogging you out. Goodbye!")
            break
        else:
            print("\nInvalid choice. Please enter 1, 2, or 3.")

def main():
    """Main function to run the application."""
    conn = connect_to_db()
    if not conn:
        return # Exit if DB connection failed

    # 1. Start with the login
    user = student_login(conn)
    
    # 2. If login is successful, show the dashboard
    if user:
        show_dashboard(conn, user)
        
    # 3. Close connection when done
    conn.close()

# --- Run the app ---
if __name__ == "__main__":
    main()