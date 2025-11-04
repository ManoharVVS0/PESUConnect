import streamlit as st
import mysql.connector
import datetime
import os
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="PESUConnect",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 1rem 0;
    }
    .metric-card {
        text-align: center;
        padding: 1rem;
        border-radius: 8px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .success-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# Database configuration
load_dotenv()

DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME')
}

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# Database connection
@st.cache_resource
def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}")
        return None

def execute_query(query, params=None, fetch=True):
    """Execute a query and return results"""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount
        cursor.close()
        return result
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        conn.rollback()
        return None

def call_procedure(proc_name, params, fetch=True):
    """Call a stored procedure"""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.callproc(proc_name, params)
        
        if fetch:
            result = []
            for res in cursor.stored_results():
                result = res.fetchall()
        else:
            conn.commit()
            result = True
            
        cursor.close()
        return result
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        conn.rollback()
        return None

# Authentication functions
def login_page():
    st.markdown('<div class="main-header">🎓 PESUConnect</div>', unsafe_allow_html=True)
    st.markdown("### Welcome to the Student Freelancing Platform")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login to Your Account")
            email = st.text_input("Email", placeholder="your.email@pesu.edu", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", type="primary", use_container_width=True):
                if email and password:
                    result = call_procedure('sp_StudentLogin', [email, password])
                    if result and len(result) > 0:
                        st.session_state.user = result[0]
                        st.session_state.page = 'dashboard'
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
                else:
                    st.warning("Please enter both email and password.")
        
        with tab2:
            st.subheader("Create New Account")
            with st.form("signup_form"):
                name = st.text_input("Full Name")
                email = st.text_input("Email", placeholder="your.email@pesu.edu")
                col_a, col_b = st.columns(2)
                with col_a:
                    password = st.text_input("Password", type="password")
                with col_b:
                    confirm_password = st.text_input("Confirm Password", type="password")
                
                phone = st.text_input("Phone Number (Optional)")
                col_c, col_d = st.columns(2)
                with col_c:
                    department = st.text_input("Department", placeholder="e.g., CSE")
                with col_d:
                    year = st.number_input("Year of Study", min_value=1, max_value=4, value=2)
                
                submit = st.form_submit_button("Sign Up", type="primary", use_container_width=True)
                
                if submit:
                    if password != confirm_password:
                        st.error("Passwords do not match!")
                    elif not all([name, email, password, department]):
                        st.warning("Please fill in all required fields.")
                    else:
                        query = """
                        INSERT INTO Student (name, email, password, phone_number, department, year_of_study)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        result = execute_query(query, (name, email, password, phone, department, year), fetch=False)
                        if result:
                            st.success("Registration successful! Please login.")
                        else:
                            st.error("Registration failed. Email might already be registered.")

# Dashboard
def dashboard():
    st.sidebar.title(f"👋 {st.session_state.user['name']}")
    st.sidebar.markdown(f"**ID:** {st.session_state.user['student_id']}")
    st.sidebar.markdown(f"**Department:** {st.session_state.user['department']}")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio(
        "Navigation",
        ["🏠 Home", "🔍 Browse Projects", "➕ Create Project", "📋 My Projects", 
         "🎯 My Skills", "📝 Active Contracts", "⭐ My Reviews"]
    )
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.page = 'login'
        st.rerun()
    
    if menu == "🏠 Home":
        show_home()
    elif menu == "🔍 Browse Projects":
        browse_projects()
    elif menu == "➕ Create Project":
        create_project()
    elif menu == "📋 My Projects":
        manage_my_projects()
    elif menu == "🎯 My Skills":
        manage_skills()
    elif menu == "📝 Active Contracts":
        view_contracts()
    elif menu == "⭐ My Reviews":
        view_reviews()

def show_home():
    st.title("🏠 Dashboard")
    
    user_id = st.session_state.user['student_id']
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        projects = execute_query("SELECT COUNT(*) as count FROM Project WHERE student_id = %s", (user_id,))
        st.metric("My Projects", projects[0]['count'] if projects else 0, "projects created")
    
    with col2:
        apps = execute_query("SELECT COUNT(*) as count FROM Application WHERE student_id = %s", (user_id,))
        st.metric("Applications", apps[0]['count'] if apps else 0, "submitted")
    
    with col3:
        contracts = execute_query(
            "SELECT COUNT(*) as count FROM Contract WHERE student_id = %s AND status = 'In Progress'", 
            (user_id,)
        )
        st.metric("Active Contracts", contracts[0]['count'] if contracts else 0, "ongoing")
    
    with col4:
        avg_rating = execute_query("SELECT fn_GetStudentAverageRating(%s) as rating", (user_id,))
        rating = avg_rating[0]['rating'] if avg_rating else 0.0
        st.metric("Average Rating", f"{rating:.2f} ⭐", "out of 5.0")
    
    st.markdown("---")
    
    # Recent activity
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Recent Applications")
        recent_apps = execute_query("""
            SELECT a.application_date, p.title, a.status
            FROM Application a
            JOIN Project p ON a.project_id = p.project_id
            WHERE a.student_id = %s
            ORDER BY a.application_date DESC
            LIMIT 5
        """, (user_id,))
        
        if recent_apps:
            for app in recent_apps:
                status_color = "🟢" if app['status'] == 'Accepted' else "🔴" if app['status'] == 'Rejected' else "🟡"
                st.markdown(f"{status_color} **{app['title']}** - {app['status']} ({app['application_date']})")
        else:
            st.info("No applications yet. Browse projects to get started!")
    
    with col_right:
        st.subheader("🔥 Open Projects")
        open_projects = execute_query("""
            SELECT project_id, title, deadline
            FROM Project
            WHERE status = 'Open' AND student_id != %s
            ORDER BY post_date DESC
            LIMIT 5
        """, (user_id,))
        
        if open_projects:
            for proj in open_projects:
                st.markdown(f"📌 **{proj['title']}** - Deadline: {proj['deadline']}")
        else:
            st.info("No open projects available.")

def browse_projects():
    st.title("🔍 Browse Available Projects")
    
    user_id = st.session_state.user['student_id']
    
    # Search and filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔎 Search projects", placeholder="Enter keywords...")
    with col2:
        status_filter = st.selectbox("Status", ["Open", "All", "In Progress", "Completed"])
    
    # Fetch projects
    if status_filter == "All":
        status_filter = None
    
    projects = call_procedure('sp_SearchProjects', [search if search else None, status_filter])
    
    if projects:
        st.markdown(f"**Found {len(projects)} project(s)**")
        
        for proj in projects:
            with st.expander(f"📋 {proj['title']} - by {proj['owner_name']}"):
                col_a, col_b = st.columns([3, 1])
                
                with col_a:
                    st.markdown(f"**Description:** {proj['description']}")
                    st.markdown(f"**Deadline:** {proj['deadline']}")
                    st.markdown(f"**Status:** {proj['status']}")
                
                with col_b:
                    if proj['status'] == 'Open':
                        if st.button("Apply Now", key=f"apply_{proj['project_id']}", type="primary"):
                            result = call_procedure('sp_CreateApplication', [user_id, proj['project_id']], fetch=False)
                            if result:
                                st.success("Application submitted!")
                                st.rerun()
                    else:
                        st.info(f"Status: {proj['status']}")
    else:
        st.info("No projects found. Try adjusting your search criteria.")

def create_project():
    st.title("➕ Create New Project")
    
    with st.form("create_project_form"):
        title = st.text_input("Project Title*")
        description = st.text_area("Project Description*", height=150)
        deadline = st.date_input("Deadline*", min_value=datetime.date.today() + datetime.timedelta(days=1))
        
        submitted = st.form_submit_button("Create Project", type="primary", use_container_width=True)
        
        if submitted:
            if title and description:
                result = call_procedure('sp_CreateProject', 
                    [st.session_state.user['student_id'], title, description, deadline], 
                    fetch=False)
                if result:
                    st.success("✅ Project created successfully!")
                    st.balloons()
            else:
                st.warning("Please fill in all required fields.")

def manage_my_projects():
    st.title("📋 My Projects")
    
    user_id = st.session_state.user['student_id']
    
    projects = execute_query("""
        SELECT 
            p.project_id, 
            p.title, 
            p.status,
            fn_GetProjectApplicationCount(p.project_id) AS pending_apps
        FROM Project p
        WHERE p.student_id = %s
        ORDER BY p.post_date DESC
    """, (user_id,))
    
    if projects:
        for proj in projects:
            with st.expander(f"📁 {proj['title']} ({proj['status']}) - {proj['pending_apps']} pending applications"):
                
                if proj['pending_apps'] > 0:
                    applications = execute_query("""
                        SELECT a.application_id, a.application_date, s.name AS applicant_name, s.student_id
                        FROM Application a
                        JOIN Student s ON a.student_id = s.student_id
                        WHERE a.project_id = %s AND a.status = 'Pending'
                    """, (proj['project_id'],))
                    
                    st.subheader("Pending Applications:")
                    for app in applications:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.write(f"**{app['applicant_name']}** - Applied on {app['application_date']}")
                        with col2:
                            if st.button("✅ Accept", key=f"accept_{app['application_id']}"):
                                result = call_procedure('sp_AcceptApplication', [app['application_id']], fetch=False)
                                if result:
                                    st.success("Application accepted!")
                                    st.rerun()
                        with col3:
                            if st.button("❌ Reject", key=f"reject_{app['application_id']}"):
                                result = call_procedure('sp_RejectApplication', [app['application_id']], fetch=False)
                                if result:
                                    st.info("Application rejected.")
                                    st.rerun()
                else:
                    st.info("No pending applications for this project.")
    else:
        st.info("You haven't created any projects yet.")

def manage_skills():
    st.title("🎯 My Skills")
    
    user_id = st.session_state.user['student_id']
    
    # Display current skills
    skills = execute_query("""
        SELECT s.skill_id, s.skill_name, ss.proficiency_level 
        FROM Student_Skill ss
        JOIN Skill s ON ss.skill_id = s.skill_id
        WHERE ss.student_id = %s
    """, (user_id,))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Skills")
        if skills:
            for skill in skills:
                col_a, col_b, col_c = st.columns([2, 1, 1])
                with col_a:
                    st.write(f"**{skill['skill_name']}**")
                with col_b:
                    st.write(f"_{skill['proficiency_level']}_")
                with col_c:
                    if st.button("🗑️", key=f"delete_{skill['skill_id']}"):
                        execute_query("DELETE FROM Student_Skill WHERE student_id = %s AND skill_id = %s", 
                                    (user_id, skill['skill_id']), fetch=False)
                        st.rerun()
        else:
            st.info("No skills added yet.")
    
    with col2:
        st.subheader("Add New Skill")
        with st.form("add_skill_form"):
            skill_name = st.text_input("Skill Name")
            proficiency = st.selectbox("Proficiency Level", ["Beginner", "Intermediate", "Advanced"])
            
            if st.form_submit_button("Add Skill", type="primary"):
                if skill_name:
                    # Check if skill exists
                    existing_skill = execute_query("SELECT skill_id FROM Skill WHERE skill_name = %s", (skill_name,))
                    
                    if existing_skill:
                        skill_id = existing_skill[0]['skill_id']
                    else:
                        # Create new skill
                        execute_query("INSERT INTO Skill (skill_name) VALUES (%s)", (skill_name,), fetch=False)
                        new_skill = execute_query("SELECT skill_id FROM Skill WHERE skill_name = %s", (skill_name,))
                        skill_id = new_skill[0]['skill_id']
                    
                    # Add to student skills
                    result = execute_query("""
                        INSERT INTO Student_Skill (student_id, skill_id, proficiency_level)
                        VALUES (%s, %s, %s)
                    """, (user_id, skill_id, proficiency), fetch=False)
                    
                    if result:
                        st.success(f"Skill '{skill_name}' added!")
                        st.rerun()

def view_contracts():
    st.title("📝 Active Contracts")
    
    user_id = st.session_state.user['student_id']
    
    # Contracts as freelancer
    st.subheader("🔨 Working On (As Freelancer)")
    freelance = execute_query("""
        SELECT 
            c.contract_id,
            p.title AS project_title,
            s.name AS project_owner_name,
            c.start_date,
            c.end_date
        FROM Contract c
        JOIN Project p ON c.project_id = p.project_id
        JOIN Student s ON p.student_id = s.student_id
        WHERE c.student_id = %s AND p.status = 'In Progress'
    """, (user_id,))
    
    if freelance:
        for contract in freelance:
            st.info(f"**{contract['project_title']}** - Owner: {contract['project_owner_name']} | "
                   f"Start: {contract['start_date']} | End: {contract['end_date']}")
    else:
        st.write("No active contracts as freelancer.")
    
    st.markdown("---")
    
    # Contracts as owner
    st.subheader("👔 Hired For (As Project Owner)")
    owner = execute_query("""
        SELECT 
            c.contract_id,
            p.title AS project_title,
            s.name AS freelancer_name,
            c.start_date,
            c.end_date
        FROM Contract c
        JOIN Project p ON c.project_id = p.project_id
        JOIN Student s ON c.student_id = s.student_id
        WHERE p.student_id = %s AND p.status = 'In Progress'
    """, (user_id,))
    
    if owner:
        for contract in owner:
            with st.expander(f"📋 {contract['project_title']} - {contract['freelancer_name']}"):
                st.write(f"Start: {contract['start_date']} | End: {contract['end_date']}")
                
                if st.button("✅ Complete Contract", key=f"complete_{contract['contract_id']}", type="primary"):
                    # Complete contract
                    result = call_procedure('sp_CompleteContract', [contract['contract_id']], fetch=False)
                    
                    if result:
                        st.success("Contract marked as complete!")
                        
                        # Review form
                        with st.form(f"review_form_{contract['contract_id']}"):
                            st.subheader("Leave a Review")
                            rating = st.slider("Rating", 1, 5, 5)
                            review_text = st.text_area("Review Comment")
                            
                            if st.form_submit_button("Submit Review"):
                                call_procedure('sp_CreateReview', 
                                    [review_text, rating, contract['contract_id'], user_id], 
                                    fetch=False)
                                
                                # Payment
                                amount = st.number_input("Payment Amount", min_value=0.0)
                                payment_method = st.text_input("Payment Method", "UPI")
                                
                                execute_query("""
                                    INSERT INTO Payment (amount, payment_date, status, payment_method, contract_id)
                                    VALUES (%s, CURDATE(), 'Paid', %s, %s)
                                """, (amount, payment_method, contract['contract_id']), fetch=False)
                                
                                st.success("Review and payment submitted!")
                                st.rerun()
    else:
        st.write("No active contracts as project owner.")

def view_reviews():
    st.title("⭐ My Reviews")
    
    user_id = st.session_state.user['student_id']
    
    # Stats
    stats = execute_query("""
        SELECT fn_GetStudentAverageRating(%s) AS avg, fn_GetStudentReviewCount(%s) AS count
    """, (user_id, user_id))
    
    if stats:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Rating", f"{stats[0]['avg']:.2f} / 5.00")
        with col2:
            st.metric("Total Reviews", stats[0]['count'])
    
    st.markdown("---")
    
    # Reviews
    reviews = execute_query("""
        SELECT r.rating, r.review_text, p.title AS project_title
        FROM Review r
        JOIN Contract c ON r.contract_id = c.contract_id
        JOIN Project p ON c.project_id = p.project_id
        WHERE r.student_id = %s
        ORDER BY c.end_date DESC
    """, (user_id,))
    
    if reviews:
        for review in reviews:
            with st.container():
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{review['project_title']}**")
                    st.write(review['review_text'])
                with col2:
                    st.markdown(f"### {'⭐' * review['rating']}")
                    st.markdown(f"**{review['rating']}/5**")
    else:
        st.info("No reviews yet. Complete some contracts to receive reviews!")

# Main app logic
def main():
    if st.session_state.user is None:
        login_page()
    else:
        dashboard()

if __name__ == "__main__":
    main()