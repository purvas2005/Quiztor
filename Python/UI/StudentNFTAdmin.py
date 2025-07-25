import streamlit as st
import requests
from datetime import date
import json
import pandas as pd
import time

# Configuration
API_URL = "http://127.0.0.1:5000"
badgeTypes = ["TopQuizzer", "PitchMaster", "TopInnovator"]

# Load student wallets
studentWallets = {}
try:
    with open("./StudentWalletMapping.json") as f:
        studentWallets = json.load(f)
except FileNotFoundError:
    st.error("StudentWalletMapping.json not found. Please create this file with student wallet mappings.")
    studentWallets = {
        "Alice Johnson": "0x123...",
        "Bob Smith": "0x456...",
        "Carol Davis": "0x789..."
    }

# Initialize session state
if 'quiz_session_id' not in st.session_state:
    st.session_state.quiz_session_id = None
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'quiz_completed' not in st.session_state:
    st.session_state.quiz_completed = False
if 'selected_student' not in st.session_state:
    st.session_state.selected_student = None
if 'quiz_results' not in st.session_state:
    st.session_state.quiz_results = None

# Helper Functions
def initialize_user(user_address):
    """Initialize user with starting tokens"""
    try:
        response = requests.post(f"{API_URL}/initialize_user", 
                               json={"user_address": user_address})
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def get_user_balance(user_address):
    """Get user token balance"""
    try:
        response = requests.get(f"{API_URL}/get_user_balance/{user_address}")
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def start_quiz(user_address):
    """Start a new quiz session"""
    try:
        response = requests.post(f"{API_URL}/start_quiz", 
                               json={"user_address": user_address})
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def get_question(session_id):
    """Get current question"""
    try:
        response = requests.get(f"{API_URL}/get_question/{session_id}")
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def submit_answer(session_id, answer):
    """Submit answer for current question"""
    try:
        response = requests.post(f"{API_URL}/submit_answer", 
                               json={"session_id": session_id, "answer": answer})
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def check_nft_eligibility(user_address):
    """Check if user can mint NFT"""
    try:
        response = requests.get(f"{API_URL}/check_nft_eligibility/{user_address}")
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def format_data_for_display(raw_data):
    """Format badge data for display"""
    formatted_data = []
    for item in raw_data:
        formatted_item = {
            "Student Name": item.get("student_name", ""),
            "Class/Semester": item.get("class_semester", ""),
            "Badge Type": item.get("badge_type", ""),
            "Grant Date": item.get("grant_date", ""),
            "University": item.get("university", ""),
            "Metadata URL": item.get('metadata_uri', ''),
            "Tokens Used": item.get('tokens_used', 'N/A')
        }
        formatted_data.append(formatted_item)
    return formatted_data

# Sidebar navigation
page = st.sidebar.radio("Menu", [
    "🏠 Home", 
    "🧠 Take Quiz", 
    "💰 Token Balance", 
    "🪙 Mint Badge NFT", 
    "🎖️ View Granted Badges"
], index=0)

st.title("🎓 Student Quiz & Badge System")

if page == "🏠 Home":
    # --- Home Page ---
    st.header("Welcome to the Student Quiz & Badge System!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 How It Works:
        1. **Take Quiz** - Answer questions to earn tokens
        2. **Earn Tokens** - Get 50 tokens per correct answer
        3. **Mint Badges** - Use 300 tokens to mint NFT badges
        4. **Track Progress** - Monitor your achievements
        """)
    
    with col2:
        st.markdown("""
        ### 📊 System Stats:
        - **Token Reward**: 50 tokens per correct answer
        - **NFT Cost**: 300 tokens minimum
        - **Starting Tokens**: 10,000 tokens
        """)

    st.subheader("📈 Badge Statistics")
    
    # Get minted counts for each badge type
    mintedCount = []
    for bType in badgeTypes:
        try:
            response = requests.get(f"{API_URL}/getMintedCount/{bType}")
            if response.status_code == 200:
                data = response.json()
                mintedCount.append({
                    "Badge Type": bType,
                    "Minted Count": data["minted_count"]
                })
        except requests.exceptions.RequestException:
            continue

    if mintedCount:
        df = pd.DataFrame(mintedCount)
        st.bar_chart(df.set_index('Badge Type'))
    else:
        st.info("No badges minted yet. Start taking quizzes to earn your first badge!")

elif page == "🧠 Take Quiz":
    # --- Quiz Page ---
    st.header("🧠 Knowledge Quiz")
    
    # Student selection
    if not st.session_state.selected_student:
        st.subheader("Select Your Profile")
        student = st.selectbox("Choose your name:", [""] + list(studentWallets.keys()))
        
        if student and st.button("Start Learning Journey"):
            st.session_state.selected_student = student
            user_address = studentWallets[student]
            
            # Initialize user
            init_result = initialize_user(user_address)
            if init_result:
                st.success(f"Welcome {student}! You have {init_result.get('tokens', 0)} tokens.")
                st.rerun()
            else:
                st.error("Failed to initialize user. Please try again.")
    
    else:
        student = st.session_state.selected_student
        user_address = studentWallets[student]
        
        # Show current balance
        balance_data = get_user_balance(user_address)
        if balance_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Tokens", balance_data.get('tokens', 0))
            with col2:
                eligibility = check_nft_eligibility(user_address)
                if eligibility:
                    st.metric("NFT Status", "✅ Eligible" if eligibility.get('eligible') else "❌ Not Eligible")
            with col3:
                if eligibility and not eligibility.get('eligible'):
                    st.metric("Tokens Needed", eligibility.get('tokens_needed', 0))
        
        # Quiz logic
        if not st.session_state.quiz_session_id and not st.session_state.quiz_completed:
            st.subheader("Ready to Test Your Knowledge?")
            st.info("Answer questions correctly to earn tokens. Each correct answer gives you 50 tokens!")
            
            if st.button("🚀 Start Quiz", type="primary"):
                quiz_data = start_quiz(user_address)
                if quiz_data:
                    st.session_state.quiz_session_id = quiz_data['session_id']
                    st.session_state.current_question = 0
                    st.session_state.quiz_completed = False
                    st.rerun()
                else:
                    st.error("Failed to start quiz. Please try again.")
        
        elif st.session_state.quiz_session_id and not st.session_state.quiz_completed:
            # Display current question
            question_data = get_question(st.session_state.quiz_session_id)
            
            if question_data and 'error' not in question_data:
                st.subheader(f"Question {question_data['question_number']} of {question_data['total_questions']}")
                st.write(question_data['question'])
                
                # Answer options
                answer = st.radio("Choose your answer:", 
                                question_data['options'], 
                                key=f"q_{st.session_state.current_question}")
                
                if st.button("Submit Answer"):
                    answer_index = question_data['options'].index(answer)
                    result = submit_answer(st.session_state.quiz_session_id, answer_index)
                    
                    if result:
                        # Show result
                        if result['correct']:
                            st.success(f"🎉 Correct! You earned {result['tokens_earned']} tokens!")
                        else:
                            correct_answer = question_data['options'][result['correct_answer']]
                            st.error(f"❌ Incorrect. The correct answer was: {correct_answer}")
                        
                        st.info(f"💰 Total tokens: {result['total_tokens']}")
                        
                        if result['quiz_completed']:
                            st.session_state.quiz_completed = True
                            st.session_state.quiz_results = result
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.session_state.current_question += 1
                            time.sleep(2)
                            st.rerun()
            else:
                st.error("Error loading question. Please restart the quiz.")
        
        elif st.session_state.quiz_completed:
            # Show quiz results
            st.subheader("🎊 Quiz Completed!")
            results = st.session_state.quiz_results
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Final Score", results.get('final_score', 'N/A'))
            with col2:
                st.metric("Tokens Earned", results.get('total_tokens_earned', 0))
            with col3:
                st.metric("Total Tokens", results.get('total_tokens', 0))
            
            if results.get('can_mint_nft'):
                st.success("🏆 Congratulations! You have enough tokens to mint an NFT badge!")
                if st.button("Go to Mint Badge", type="primary"):
                    st.session_state.quiz_session_id = None
                    st.session_state.quiz_completed = False
                    st.session_state.quiz_results = None
                    st.switch_page = "🪙 Mint Badge NFT"
            else:
                tokens_needed = 300 - results.get('total_tokens', 0)
                st.info(f"Keep learning! You need {tokens_needed} more tokens to mint an NFT.")
            
            if st.button("Take Another Quiz"):
                st.session_state.quiz_session_id = None
                st.session_state.quiz_completed = False
                st.session_state.quiz_results = None
                st.rerun()
        
        # Reset button
        if st.button("🔄 Reset Session"):
            st.session_state.selected_student = None
            st.session_state.quiz_session_id = None
            st.session_state.quiz_completed = False
            st.session_state.quiz_results = None
            st.rerun()

elif page == "💰 Token Balance":
    # --- Token Balance Page ---
    st.header("💰 Token Management")
    
    student = st.selectbox("Select Student:", [""] + list(studentWallets.keys()))
    
    if student:
        user_address = studentWallets[student]
        
        # Get balance
        balance_data = get_user_balance(user_address)
        eligibility_data = check_nft_eligibility(user_address)
        
        if balance_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("💎 Current Token Balance", balance_data.get('tokens', 0))
                
            with col2:
                if eligibility_data:
                    if eligibility_data.get('eligible'):
                        st.success("✅ Eligible for NFT Minting")
                    else:
                        st.warning(f"❌ Need {eligibility_data.get('tokens_needed', 0)} more tokens")
            
            # Token history (mock data for demonstration)
            st.subheader("📊 Token Activity")
            token_history = pd.DataFrame({
                'Date': ['2025-06-01', '2025-06-02', '2025-06-03'],
                'Activity': ['Quiz Completed', 'Quiz Completed', 'NFT Minted'],
                'Tokens': ['+150', '+200', '-300'],
                'Balance': [10150, 10350, 10050]
            })
            st.dataframe(token_history, use_container_width=True)
        
        # Initialize user button
        if st.button(f"Initialize {student}"):
            init_result = initialize_user(user_address)
            if init_result:
                st.success(f"User initialized with {init_result.get('tokens', 0)} tokens!")
                st.rerun()
            else:
                st.error("Failed to initialize user.")

elif page == "🪙 Mint Badge NFT":
    # --- Enhanced Mint Badge Page ---
    st.header("🪙 Mint Badge NFT")
    
    badge_type = st.selectbox("Select Badge Type", badgeTypes)
    student = st.selectbox("Select Student", [""] + list(studentWallets.keys()))
    
    if student:
        user_address = studentWallets[student]
        
        # Check eligibility
        eligibility = check_nft_eligibility(user_address)
        balance_data = get_user_balance(user_address)
        
        if eligibility and balance_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Tokens", balance_data.get('tokens', 0))
            with col2:
                st.metric("Required Tokens", 300)
            with col3:
                if eligibility.get('eligible'):
                    st.success("✅ Eligible")
                else:
                    st.error(f"❌ Need {eligibility.get('tokens_needed', 0)} more")
        
        if eligibility and eligibility.get('eligible'):
            # Student details form
            with st.form("mint_badge_form"):
                st.subheader("Student Information")
                studentClass = st.text_input("Class/Semester", placeholder="Enter Class/Semester")
                studentUniversity = st.text_input("University", placeholder="Enter University Name")
                
                submitButton = st.form_submit_button("🎖️ Mint Badge NFT", type="primary")
                
                if submitButton and studentClass and studentUniversity:
                    with st.spinner("Minting your NFT badge..."):
                        # Upload metadata
                        payload = {
                            "student_name": student,
                            "class_semester": studentClass,
                            "university": studentUniversity,
                            "badge_type": badge_type,
                            "user_address": user_address
                        }
                        
                        response = requests.post(f"{API_URL}/uploadMetadata", json=payload)
                        
                        if response.status_code == 200:
                            metaDataURI = response.json().get("metadata_uri")
                            st.success(f"✅ Metadata uploaded! IPFS URI: {metaDataURI}")
                            
                            # Mint the badge
                            badgeData = {
                                "recipient": user_address,
                                "badge_type": badge_type,
                                "token_uri": metaDataURI,
                                "user_address": user_address
                            }
                            
                            mintStatus = requests.post(f"{API_URL}/mintBadge", json=badgeData)
                            
                            if mintStatus.status_code == 200:
                                mint_result = mintStatus.json()
                                st.success(f"🎉 Badge minted successfully!")
                                st.info(f"Transaction Hash: {mint_result.get('tx_hash')}")
                                st.info(f"Tokens Used: {mint_result.get('tokens_deducted', 300)}")
                                st.info(f"Remaining Tokens: {mint_result.get('remaining_tokens', 0)}")
                                st.balloons()
                            else:
                                error_msg = mintStatus.json().get('error', 'Unknown error')
                                st.error(f"❌ Minting failed: {error_msg}")
                        else:
                            error_msg = response.json().get('error', 'Unknown error')
                            st.error(f"❌ Metadata upload failed: {error_msg}")
        else:
            st.warning("⚠️ This student doesn't have enough tokens to mint an NFT. They need to take more quizzes!")
            if eligibility:
                st.info(f"Tokens needed: {eligibility.get('tokens_needed', 0)}")

elif page == "🎖️ View Granted Badges":
    # --- Enhanced View Badges Page ---
    st.header("🎖️ View Granted Badges")
    
    try:
        response = requests.get(f"{API_URL}/list_minted_badges")
        
        if response.status_code == 200:
            data = response.json()
            
            if not data or data == 0:
                st.info("🚀 No badges granted yet. Start taking quizzes to earn your first badge!")
            else:
                st.success(f"📊 Total badges minted: {len(data)}")
                
                # Create enhanced dataframe
                cols_order = [
                    "Student Name", 
                    "Badge Grant Date", 
                    "Badge Type", 
                    "Class or Semester", 
                    "University", 
                    "Tokens Used",
                    "Certificate URL"
                ]
                
                df = pd.DataFrame(data)
                if not df.empty and all(col in df.columns for col in cols_order):
                    df = df[cols_order]
                    
                    # Add filters
                    st.subheader("🔍 Filter Badges")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        badge_filter = st.selectbox("Filter by Badge Type:", 
                                                  ["All"] + badgeTypes)
                    with col2:
                        student_filter = st.selectbox("Filter by Student:", 
                                                    ["All"] + df["Student Name"].unique().tolist())
                    
                    # Apply filters
                    filtered_df = df.copy()
                    if badge_filter != "All":
                        filtered_df = filtered_df[filtered_df["Badge Type"] == badge_filter]
                    if student_filter != "All":
                        filtered_df = filtered_df[filtered_df["Student Name"] == student_filter]
                    
                    # Display results
                    st.subheader(f"📋 Badge Records ({len(filtered_df)} records)")
                    st.dataframe(filtered_df, use_container_width=True)
                    
                    # Download option
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="student_badges.csv",
                        mime="text/csv"
                    )
                else:
                    st.dataframe(df, use_container_width=True)
        else:
            st.error(f"❌ Failed to fetch badge data: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Connection error: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 System Status")
try:
    response = requests.get(f"{API_URL}/get_user_balance/test", timeout=5)
    if response.status_code in [200, 400]:  # API is responding
        st.sidebar.success("✅ API Connected")
    else:
        st.sidebar.error("❌ API Issues")
except:
    st.sidebar.error("❌ API Offline")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip**: Take quizzes regularly to earn tokens and unlock exclusive NFT badges!")
