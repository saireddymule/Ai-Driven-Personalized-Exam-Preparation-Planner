import streamlit as st
import os
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta, time
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ---------------- SESSION INITIALIZATION ---------------- #

def init_session():
    defaults = {
        "page": "Home",
        "plan_generated": False,
        "plan_output": "",
        "days_remaining": 0,
        "duration_weeks": 0,
        "daily_hours": 0,
        "exam_subject": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_home_background(image_path):

    if image_path.startswith("http"):
        bg_url = image_path
    else:
        import base64
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
        bg_url = f"data:image/jpg;base64,{encoded}"

    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("{bg_url}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        [data-testid="stHeader"] {{
            background: rgba(0,0,0,0);
        }}

        [data-testid="stToolbar"] {{
            right: 2rem;
        }}

        .block-container {{
            background-color: rgba(0, 0, 0, 0.65);
            padding: 2rem;
            border-radius: 15px;
        }}

        h1, h2, h3, p {{
            color: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
# ---------------- STUDY PLAN GENERATOR ---------------- #

def generate_study_plan(inputs):

    try:
        llm = ChatGroq(
            temperature=0.7,
            model_name="openai/gpt-oss-120b",
            api_key=key  # Replace with env variable in production
        )

        system_prompt = (
            "You are an expert AI Exam Preparation Planner. "
            "Generate a detailed structured plan in Markdown. "
            "Do not add intro or conclusion outside structured content."
        )

        template = """
        Generate a detailed study plan:

        Exam: {exam_subject}
        Duration: {duration_weeks} days
        Daily Study Hours: {daily_hours}
        Weaknesses: {weaknesses}
        Learning Style: {learning_style}
        Exam Type: {exam_type}

        Structure:
        1. keep a table with Topics with Basic,Intermediate and Advance levels don't use bullet points 
        2. Based on given Duration: {duration_weeks} weeks Detailed Plan (AM/PM timing) also mention break timings in table
        3. Practice Strategy
        4. Revision Loop 
        5. Suggested Resources prefer free online resources and for youtube prefer 3blue1brown channel provide links
        6. Motivation Tips
        7. Backup Plan
        """

        chat_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", template),
        ])

        chain = chat_template | llm | StrOutputParser()

        return chain.invoke(inputs)

    except Exception as e:
        print(e)
        st.error("Api key is Missing")
        return f"ERROR: {e}"
    


# ---------------- HOME PAGE ---------------- #

def home_page():
    st.title("🎯 AI Driven Personalized Exam Preparation Planner")
    # st.write("Generate a strategic study plan powered by Groq LLM.")
    set_home_background("bg2.jpeg")  # or paste URL instead
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚀 Start Planning"):
            st.session_state.page = "Planner"
            st.rerun()

    with col2:
        if st.button("📊 Progress Tracker"):
            st.session_state.page = "Progress Tracker"
            st.rerun()

    with col3:
        if st.button("📊 View Analytics"):
            st.session_state.page = "Analytics"
            st.rerun()
# ---------------- PLANNER PAGE ---------------- #

def planner_page():
    st.title("📚 Study Plan Generator")
    set_home_background("bg2.jpeg")  # or paste URL instead

    with st.form("exam_form"):

        exam_subject = st.text_input("Exam / Subject Name")

        exam_date = st.date_input("Exam Date", min_value=date.today())

        col1, col2 = st.columns(2)

        with col1:
            start_time = st.time_input("Study Start Time", value=time(18, 0))
        with col2:
            end_time = st.time_input("Study End Time", value=time(21, 0))

        learning_style = st.multiselect(
            "Learning Style",
            ["Visual", "Auditory", "Kinesthetic", "Reading/Writing"]
        )

        weaknesses = st.text_area("Weaknesses")
        exam_type = st.text_input("Exam Type")

        submit_button = st.form_submit_button("Generate Study Plan")

    # ----------- PLAN GENERATION ----------- #

    if submit_button:

        if not exam_subject or not weaknesses:
            st.warning("Please fill required fields.")
            return

        days_remaining = (exam_date - date.today()).days
        duration_weeks = round(days_remaining / 7, 1)

        start_dt = datetime.combine(datetime.today(), start_time)
        end_dt = datetime.combine(datetime.today(), end_time)

        if end_dt <= start_dt:
            end_dt += timedelta(days=1)

        daily_hours = round((end_dt - start_dt).total_seconds() / 3600, 2)

        inputs = {
            "exam_subject": exam_subject,
            "duration_weeks": duration_weeks,
            "daily_hours": daily_hours,
            "weaknesses": weaknesses,
            "learning_style": learning_style,
            "exam_type": exam_type,
        }

        with st.spinner("Generating plan..."):
            plan_output = generate_study_plan(inputs)

        if not plan_output.startswith("ERROR"):
            st.session_state.plan_generated = True
            st.session_state.plan_output = plan_output
            st.session_state.days_remaining = days_remaining
            st.session_state.duration_weeks = duration_weeks
            st.session_state.daily_hours = daily_hours
            st.session_state.exam_subject = exam_subject

    # ----------- DISPLAY PLAN ----------- #

    if st.session_state.plan_generated:

        st.success(f"📅 {st.session_state.days_remaining} days remaining")
        st.info(f"⏰ {st.session_state.daily_hours} hours per day available")

        st.markdown("### ✅ Generated Study Plan")
        st.markdown(st.session_state.plan_output)

        # ----------- FEEDBACK SECTION ----------- #

        st.markdown("---")
        st.subheader("⭐ Give Your Feedback")

        with st.form("feedback_form"):

            feedback_text = st.text_area("Your Feedback")
            rating = st.slider("Rating (1-5)", 1, 5)

            feedback_submit = st.form_submit_button("Submit Feedback")

            if feedback_submit:

                feedback_data = {
                    "Exam": st.session_state.exam_subject,
                    "Rating": rating,
                    "Feedback": feedback_text
                }

                df = pd.DataFrame([feedback_data])

                if os.path.exists("feedback.csv"):
                    df.to_csv("feedback.csv", mode="a", header=False, index=False)
                else:
                    df.to_csv("feedback.csv", index=False)

                st.success("Thank you for your feedback!")

def progress_tracker_page():
    st.title("📈 Study Progress Tracker")
    set_home_background("bg2.jpeg")  # or paste URL instead

    if not st.session_state.plan_generated:
        st.warning("Please generate a study plan first.")
        return

    st.subheader("📝 Log Today's Study Progress")

    with st.form("progress_form"):

        study_date = st.date_input("Select Date", value=date.today())
        hours_completed = st.number_input("Hours Studied", min_value=0.0, max_value=24.0, step=0.5)
        completion_status = st.selectbox(
            "Completion Status",
            ["Completed", "Partially Completed", "Missed"]
        )
        notes = st.text_area("Notes (Optional)")

        submit_progress = st.form_submit_button("Save Progress")

        if submit_progress:

            progress_data = {
                "Exam": st.session_state.exam_subject,
                "Date": study_date,
                "Planned Hours": st.session_state.daily_hours,
                "Completed Hours": hours_completed,
                "Status": completion_status,
                "Notes": notes
            }

            df = pd.DataFrame([progress_data])

            if os.path.exists("progress_log.csv"):
                df.to_csv("progress_log.csv", mode="a", header=False, index=False)
            else:
                df.to_csv("progress_log.csv", index=False)

            st.success("Progress saved successfully!")

    st.markdown("---")
    st.subheader("📊 Progress Overview")

    if os.path.exists("progress_log.csv"):

        df = pd.read_csv("progress_log.csv")

        if "Exam" in df.columns:
            df = df[df["Exam"] == st.session_state.exam_subject]

        if len(df) == 0:
            st.info("No progress logged yet.")
            return

        df["Completed Hours"] = pd.to_numeric(df["Completed Hours"], errors="coerce")

        # Total Stats
        total_days = len(df)
        completed_days = len(df[df["Status"] == "Completed"])
        completion_rate = round((completed_days / total_days) * 100, 2)

        st.metric("Total Study Days Logged", total_days)
        st.metric("Completion Rate (%)", completion_rate)

        st.write("### 📈 Hours Studied Over Time")
        st.line_chart(df.set_index("Date")["Completed Hours"])

        st.write("### 🟢 Status Distribution")
        st.bar_chart(df["Status"].value_counts())

    else:
        st.info("No progress data available yet.")

# ---------------- ANALYTICS PAGE ---------------- #

def analytics_page():
    st.title("📊 User Feedback Analytics")
    set_home_background("bg2.jpeg")  # or paste URL instead

    if os.path.exists("feedback.csv"):
        columns=["Exam", "Rating", "Feedback"]
        df = pd.read_csv("feedback.csv")
        df.columns=columns
        st.write("### Raw Feedback Data")
        st.dataframe(df)

        # Ensure required columns exist
        required_columns = ["Exam", "Rating", "Feedback"]

        if not all(col in df.columns for col in required_columns):
            st.error("⚠️ feedback.csv format is incorrect.")
            st.write("Expected columns:", required_columns)
            st.write("Found columns:", list(df.columns))
            return

        # Convert Rating to numeric (safe)
        df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")

        st.write("### 📈 Average Rating")
        st.metric("Average Rating", round(df["Rating"].mean(), 2))

        st.write("### ⭐ Rating Distribution")
        st.bar_chart(df["Rating"].value_counts(),color='#2af01f')
        # fig = px.bar(df, values='Rating',  title='Rating Distribution')
        # st.plotly_chart(fig)


    else:
        st.info("No feedback available yet.")

# ---------------- MAIN APP ---------------- #

st.set_page_config(page_title="Aura Learn", layout="wide")

init_session()

with st.sidebar:
    st.title("Navigation")
    key=st.text_input(label="Api Key",type="password",help="Get your Api Key from groq cloud")
    if not key:
        st.warning("Paste Your Api Key")

    selected_page = st.radio(
        "Go to",
        ["Home", "Planner","Progress Tracker", "Analytics"],
        index=["Home", "Planner", "Progress Tracker","Analytics"].index(st.session_state.page)
    )

    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.rerun()

if st.session_state.page == "Home":
    home_page()

elif st.session_state.page == "Planner":
    planner_page()

elif st.session_state.page == "Progress Tracker":
    progress_tracker_page()

elif st.session_state.page == "Analytics":
    analytics_page()