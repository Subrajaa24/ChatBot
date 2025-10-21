import streamlit as st
import sqlite3
import bcrypt
import time
import pandas as pd 
import sqlite3.dbapi2 as sqlite # Alias for clarity in DB storage

# ==============================
# PAGE CONFIGURATION
# ==============================
# Use 'wide' layout and set the initial title
st.set_page_config(page_title="BuddyBot", page_icon="🤖", layout="wide")

# ==============================
# DATABASE SETUP
# ==============================
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        filename TEXT,
        domain TEXT,  
        data BLOB
    )
""")
conn.commit()

# ==============================
# DOMAIN DATA
# ==============================
DOMAINS = {
    "Sports": {
        "icon": "⚽",
        "description": "Analyze team stats, game history, and player performance.",
    },
    "Education": {
        "icon": "📚",
        "description": "Create learning assistants from textbooks, notes, or research papers.",
    },
    "Art & Design": {
        "icon": "🎨",
        "description": "Interpret artistic styles, history, or design principles.",
    },
    "Entertainment": {
        "icon": "🎬",
        "description": "Discuss movies, music, celebrities, and pop culture trends.",
    },
    "Business": {
        "icon": "💼",
        "description": "Handle customer FAQs, process financial reports, or analyze market data.",
    }
}

# ==============================
# PAGE STYLING
# ==============================
st.markdown("""
    <style>
        /* Base Styling */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #0b1a37 0%, #1c2b4d 100%);
            color: white;
            animation: fadeIn 1s ease-in-out;
        }
        .title {
            text-align: center;
            font-size: 36px;
            font-weight: 800;
            color: #6EC6FF;
            margin-bottom: 20px;
        }
        
        /* Sidebar Bot Avatar */
        .sidebar-bot-avatar {
            text-align: center;
            margin-bottom: 20px;
        }
        .sidebar-bot-avatar img {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background-color: #6EC6FF;
            padding: 5px;
            box-shadow: 0 0 10px rgba(110, 198, 255, 0.5);
        }
        .sidebar-bot-avatar p {
            font-size: 18px;
            font-weight: bold;
            color: white;
            margin-top: 10px;
        }
        
        /* Logo & Chat Bubbles */
        .logo-container {
            text-align: center;
            margin-top: 30px;
            animation: slideUp 1s ease-in-out;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(40px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .chat-bubble {
            background-color: #2b70f0;
            border-radius: 15px;
            padding: 10px 15px;
            display: inline-block;
            margin: 10px 0;
            color: white;
            max-width: 90%;
            text-align: left;
        }
        .chat-bubble-container {
            margin-top: 20px;
            width: 100%;
            text-align: center;
        }

        /* Input & Auth Button Styles */
        .stTextInput > div > div > input, .stSelectbox > div > div > div > input {
            background-color: #1c2b4d;
            border: 1px solid #334466;
            color: white;
            transition: all 0.2s ease;
        }
        .stTextInput > div > div > input:focus, .stTextInput > div > div > input:hover {
            border-color: #6EC6FF !important;
            box-shadow: 0 0 0 1px #6EC6FF;
        }
        div.stButton button[kind="primary"] {
            background-color: white !important;
            color: #2b70f0 !important;
            border: 1px solid #2b70f0;
            font-weight: bold;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            transition: all 0.3s ease-in-out;
        }
        div.stButton button[kind="primary"]:hover {
            background-color: #f0f0f0 !important;
            transform: scale(1.02);
            border-color: #1748b0;
        }
        
        /* Custom Styling for Simple Domain Cards/Buttons */
        .domain-card {
            background-color: #1c2b4d;
            border: 2px solid #334466;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        .domain-card:hover {
            border-color: #6EC6FF;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.5);
            transform: translateY(-3px);
        }
        .domain-card h3 {
            color: #6EC6FF;
            margin-top: 0;
            font-size: 20px;
        }
        .domain-card p {
            font-size: 14px;
            color: #ccc;
        }
        
        /* Sidebar styling for better appearance */
        [data-testid="stSidebar"] {
            background-color: #1c2b4d !important;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================
# SESSION STATE & NAVIGATION HELPERS
# ==============================
if 'page' not in st.session_state:
    st.session_state.page = 'register'
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'selected_domain' not in st.session_state:
    st.session_state.selected_domain = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {} # Key is domain, value is list of messages

# Check query parameters for initial navigation
if 'page' in st.query_params:
    st.session_state.page = st.query_params['page']

# Navigation Functions
def navigate_to_login():
    st.session_state.page = 'login'
    st.query_params['page'] = 'login'

def navigate_to_register():
    st.session_state.page = 'register'
    st.query_params['page'] = 'register'

def navigate_to_upload():
    st.session_state.page = 'upload'
    st.query_params['page'] = 'upload'

def navigate_to_policy():
    st.session_state.page = 'policy'
    st.query_params['page'] = 'policy'
    
# Callback function for domain selection
def select_domain_callback(domain_name):
    st.session_state.selected_domain = domain_name
    # Load history for the selected domain, or initialize it
    if domain_name not in st.session_state.chat_history:
        st.session_state.chat_history[domain_name] = []
    st.session_state.messages = st.session_state.chat_history[domain_name]
    st.rerun() 

# ==============================
# SIDEBAR CONTENT FUNCTION
# ==============================
def show_sidebar_content():
    # Only show this content when logged in and on the upload/chat page
    if 'logged_in_email' not in st.session_state or st.session_state.page != 'upload':
        return

    user_email = st.session_state.logged_in_email
    domain = st.session_state.selected_domain
    
    # 1. Bot Avatar & Name
    st.sidebar.markdown("""
        <div class="sidebar-bot-avatar">
            <img src="https://cdn-icons-png.flaticon.com/512/4712/4712100.png" alt="Bot Avatar">
            <p>BuddyBot</p>
        </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    # 2. User Info & Logout
    # Display the user email clearly
    st.sidebar.markdown(f"**User:** `{user_email}`")
    
    # Logout button functionality
    st.sidebar.button("Logout", key="logout_sidebar", use_container_width=True, on_click=lambda: (
        st.session_state.pop('logged_in_email', None), 
        st.session_state.pop('selected_domain', None),
        st.session_state.messages.clear(), 
        st.session_state.chat_history.clear(), # Clear all history on logout
        navigate_to_login(),
        st.rerun()
    ))
    st.sidebar.markdown("---")

    # 3. Help Section
    with st.sidebar.expander("❓ **Help Section**"):
        st.markdown("1. **Select Domain** to specialize the bot.")
        st.markdown("2. **Upload a CSV** to train the bot.")
        st.markdown("3. **Chat** with your customized bot.")
        st.markdown("4. Use **History** to review past chats.")
    st.sidebar.markdown("---")

    # 4. History of the User (Based on Domain)
    if domain:
        st.sidebar.markdown(f"**Chat History: {domain}**")
        if st.session_state.chat_history.get(domain):
            # Display history in a scrollable container
            with st.sidebar.container(height=200):
                for i, msg in enumerate(st.session_state.chat_history[domain]):
                    # Display only the first few words of the user's prompt as a history item
                    if msg["role"] == "user":
                        summary = msg["content"][:30] + "..." if len(msg["content"]) > 30 else msg["content"]
                        st.sidebar.markdown(f"*{i+1}. {summary}*")
        else:
            st.sidebar.markdown("No history for this domain yet.")
    else:
        st.sidebar.markdown("**Select a domain to view chat history.**")
    st.sidebar.markdown("---")


# ==============================
# CHAT LOGIC
# ==============================
def display_chat_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_chat_input(domain):
    domain_display = DOMAINS.get(domain, {}).get("icon", "") + " " + domain
    
    if prompt := st.chat_input(f"Chat with your {domain} Bot..."):
        # Save user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.chat_history[domain] = st.session_state.messages
        
        with st.chat_message("assistant"):
            response = f"I see you're interested in **{domain_display}**! To answer your question, '{prompt}', I need to load your training dataset first."
            st.markdown(response)
            
            # Save assistant message
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.chat_history[domain] = st.session_state.messages
            
        # Rerun to update chat history in the sidebar immediately
        st.rerun() 

# ==============================
# DOMAIN SELECTION PAGE
# ==============================
def show_domain_selection_page():
    st.markdown("<div class='title'>1. Select Your Bot's Domain</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    domain_names = list(DOMAINS.keys())
    
    for i in range(0, len(domain_names), 3):
        cols = st.columns(3)
        
        for j in range(3):
            if i + j < len(domain_names):
                domain_name = domain_names[i + j]
                data = DOMAINS[domain_name]
                
                with cols[j]:
                    st.markdown(f"""
                    <div class="domain-card">
                        <h3>{data['icon']} {domain_name}</h3>
                        <p>{data['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.button(
                        "Select Domain",
                        key=f"select_domain_btn_{domain_name.lower().replace(' ', '_')}",
                        use_container_width=True,
                        type="primary",
                        on_click=select_domain_callback,
                        args=(domain_name,)
                    )
                    st.markdown("<br>", unsafe_allow_html=True)

# ==============================
# AUTH & REGISTRATION PAGES (Full logic restored)
# ==============================
def show_register_page():
    st.markdown("<div class='title'>Welcome to Sign Up <span style='color:#6EC6FF;'>Buddy!</span></div>", unsafe_allow_html=True)

    with st.form(key="register_form"):
        name = st.text_input("Enter your name", key="reg_name")
        email = st.text_input("Enter your email", key="reg_email")
        password = st.text_input("Enter your password", type="password", key="reg_password")
        
        # Link to Policy
        st.markdown(
            "By signing up, you agree to our <a href='?page=policy'>Terms and Privacy Policy</a>.", 
            unsafe_allow_html=True
        )
        agree = st.checkbox("I confirm I have read and agree to the policy.", key="register_agree_checkbox")

        if st.form_submit_button("Sign Up", type="primary", use_container_width=True):
            if name and email and password and agree:
                hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                try:
                    cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_pw))
                    conn.commit()
                    st.success("🎉 Registration successful! Please login.")
                    navigate_to_login()
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("⚠️ Email already exists.")
            else:
                st.warning("⚠️ Fill all fields and confirm agreement to terms to continue.")

    st.markdown('<div style="text-align:center;">Already have an account?</div>', unsafe_allow_html=True)
    if st.button("Sign In", use_container_width=True, key="go_to_login_btn"):
        navigate_to_login()
        st.rerun()


def show_login_page():
    st.markdown("<div class='title'>Welcome Back, <span style='color:#6EC6FF;'>Buddy!</span></div>", unsafe_allow_html=True)

    with st.form(key="login_form"):
        email = st.text_input("Enter your email", key="log_email")
        password = st.text_input("Enter your password", type="password", key="log_password")

        if st.form_submit_button("Sign In", type="primary", use_container_width=True):
            cursor.execute("SELECT password, email FROM users WHERE email=?", (email,))
            user_data = cursor.fetchone()
            
            if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data[0]):
                st.success("✅ Login successful! Redirecting...")
                st.session_state.logged_in_email = user_data[1] 
                navigate_to_upload()
                st.rerun()
            else:
                st.error("❌ Invalid email or password.")

    st.markdown('<div style="text-align:center;">Don\'t have an account?</div>', unsafe_allow_html=True)
    if st.button("Sign Up", use_container_width=True, key="go_to_register_btn"):
        navigate_to_register()
        st.rerun()

def show_policy_page(): 
    st.markdown("<div class='title'>Terms and Privacy</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
        <div style="padding: 0 20px; text-align: left;">
        
        <h2>1. Terms of Service</h2>
        <p>Welcome to Buddy! By using our service, you agree to these Terms. Please read them carefully.</p>
        
        <h4>Account Responsibility</h4>
        <p>You are responsible for all activity under your account. You must keep your password secure and notify us immediately of any unauthorized use.</p>
        
        <h4>User Conduct</h4>
        <p>You agree not to use the Service for any unlawful or prohibited activities, including the transmission of harassing, hateful, or abusive content.</p>
        
        <h2>2. Privacy Policy</h2>
        <p>We take your privacy seriously. This policy describes how we collect, use, and handle your information.</p>
        
        <h4>Data Collection</h4>
        <p>We collect personal information you provide directly to us, suchs as your name, email address, and interactions with the 'Buddy' AI.</p>
        
        <h4>Data Usage</h4>
        <p>We use your data to operate, maintain, and improve our services. We do not sell your personal data to third parties.</p>
        
        </div>
    """, unsafe_allow_html=True)

    if st.button("← Back to Registration", key="back_to_reg"):
        navigate_to_register()
        st.rerun()


# ==============================
# WORKSPACE / UPLOAD PAGE
# ==============================
def show_upload_page():
    
    if 'logged_in_email' not in st.session_state:
        st.error("Access Denied. Please log in first.")
        navigate_to_login()
        st.rerun()
        return

    # Call the new sidebar function
    show_sidebar_content()

    user_email = st.session_state.logged_in_email
    
    # --- Phase 1: Domain Selection ---
    if st.session_state.selected_domain is None:
        show_domain_selection_page()
        
    # --- Phase 2: Bot Setup and Chat ---
    else:
        domain = st.session_state.selected_domain
        domain_data = DOMAINS.get(domain, {"icon": "", "description": ""})
        domain_display = domain_data["icon"] + " " + domain
        
        st.markdown(f"<div class='title'>🤖 {domain_display} Bot Workspace</div>", unsafe_allow_html=True)
        st.markdown(f"**Goal:** Train your bot for **{domain_data['description']}**", unsafe_allow_html=True)
        st.markdown("---")
        
        col_left, col_right = st.columns([1, 1.5])
        
        # --- LEFT COLUMN: Dataset Uploader ---
        with col_left:
            st.subheader("2. Upload Training Dataset")
            file = st.file_uploader("Upload a CSV dataset", type=["csv"], key="dataset_uploader")
            
            if st.button(f"Train Bot for {domain}", use_container_width=True, type="primary", key="train_btn"):
                if file is None:
                    st.error("⚠️ Please upload a CSV dataset before training.")
                else:
                    try:
                        df = pd.read_csv(file)
                        st.subheader("Dataset Preview")
                        st.dataframe(df.head())
                        
                        # Store dataset in DB
                        file_data_bytes = file.getvalue()
                        # Use sqlite.Binary for BLOB storage
                        cursor.execute("""
                            INSERT INTO datasets (user_email, filename, domain, data) 
                            VALUES (?, ?, ?, ?)
                        """, (user_email, file.name, domain, sqlite.Binary(file_data_bytes)))
                        conn.commit()
                        
                        st.success(f"✅ Success! Data for **{domain}** saved. Start chatting on the right!")
                        
                    except Exception as e:
                        st.error(f"Error processing or saving dataset: {e}")
                        
            st.markdown("---")
            if st.button("← Change Domain", key="change_domain_btn"):
                st.session_state.selected_domain = None
                st.session_state.messages = [] 
                st.rerun()

        # --- RIGHT COLUMN: Chat Section ---
        with col_right:
            st.subheader("3. Chat Interface")
            
            # Chat messages container
            with st.container(height=400):
                 display_chat_messages()

            # Chat input field
            handle_chat_input(domain)
            

# ==============================
# PAGE LAYOUT EXECUTION
# ==============================
if st.session_state.page == 'upload':
    show_upload_page()
else:
    # Landing page for Register/Login/Policy
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown('<div class="logo-container"><img src="https://cdn-icons-png.flaticon.com/512/4712/4712100.png" width="150"></div>', unsafe_allow_html=True)
        st.markdown("""
            <div class='chat-bubble-container'>
                <div class='chat-bubble'>Hello, can you help me?</div><br>
                <div class='chat-bubble'>Of course! Buddy is ready to assist.</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        if st.session_state.page == 'register':
            show_register_page()
        elif st.session_state.page == 'login':
            show_login_page()
        elif st.session_state.page == 'policy':
            show_policy_page() 
        st.markdown("</div>", unsafe_allow_html=True)