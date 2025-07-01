import streamlit as st
import random
import requests
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import os
from transformers import T5Tokenizer, T5ForConditionalGeneration

tokenizer = T5Tokenizer.from_pretrained("iarfmoose/t5-base-question-generator", use_fast=False)
model = T5ForConditionalGeneration.from_pretrained("iarfmoose/t5-base-question-generator")

os.environ["TRANSFORMERS_CACHE"] = "/app/.cache/huggingface"
# Load question-generation model
@st.cache_resource

def load_qg_model():
    tokenizer = AutoTokenizer.from_pretrained("iarfmoose/t5-base-question-generator", use_fast=False)
    model = AutoModelForSeq2SeqLM.from_pretrained("iarfmoose/t5-base-question-generator")
    return pipeline("text2text-generation", model=model, tokenizer=tokenizer)


qg_pipeline = load_qg_model()

# Supported languages and translations
LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te"
}

LABELS = {
    "en": {
        "welcome": "Welcome to your smart Wikipedia-powered quiz companion!",
        "start_quiz": "▶️ Start New Quiz",
        "question": "Question",
        "desc": "Answer the following question:",
        "submit": "✅ Submit Answer",
        "correct": "✅ Correct!",
        "incorrect": "❌ Incorrect! Correct answer:",
        "completed": "🎉 Quiz completed! Final Score:",
        "restart": "🔄 Restart",
        "choose_topic": "Choose a topic",
        "select_difficulty": "🔥 Select Difficulty"
    }
    # Hindi and Telugu omitted for brevity. Add as needed.
}

TOPICS = [
    "Artificial intelligence", "Mahatma Gandhi", "The Solar System",
    "Indian Constitution", "Python programming", "Photosynthesis"
]

# Session state initialization
for key, value in {
    "quiz_started": False,
    "score": 0,
    "current_q": 0,
    "question_bank": [],
    "selected_topic": "",
    "selected_lang": "en",
    "difficulty": "Medium",
    "num_questions": 5
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Page setup
st.set_page_config(page_title="WikiWhiz AI Quiz", layout="centered")

# Sidebar
lang_ui = st.sidebar.selectbox("🌐 Choose Language / भाषा / భాష", list(LANGUAGES.keys()))
lang = LANGUAGES[lang_ui]
labels = LABELS[lang]
st.session_state.selected_lang = lang

# Header
st.image("https://upload.wikimedia.org/wikipedia/commons/6/63/Wikipedia-logo.png", width=70)
st.markdown("<h1 style='text-align: center;'>🧠 WikiWhiz – AI Quizipedia</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>{labels['welcome']}</p>", unsafe_allow_html=True)
st.markdown("---")

# Pre-quiz selections
if not st.session_state.quiz_started:
    with st.container():
        st.session_state.difficulty = st.select_slider(
            f"🔥 {labels['select_difficulty']}",
            options=["Easy", "Medium", "Hard"],
            value="Medium"
        )
        selected_topic = st.selectbox(f"🎯 {labels['choose_topic']}", TOPICS)
        st.session_state.selected_topic = selected_topic

        num_questions = st.slider("📝 Number of Questions", min_value=3, max_value=10, value=5)
        st.session_state.num_questions = num_questions

# Wikipedia summary fetch
@st.cache_data(show_spinner=False)
def get_summary(topic):
    try:
        response = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/" + topic.replace(" ", "%20")
        )
        return response.json().get("extract", "")
    except:
        return ""

# Generate AI questions
@st.cache_data(show_spinner=False)
def generate_ai_questions(context, n=5):
    qa_pairs = qg_pipeline(context)
    random.shuffle(qa_pairs)
    return qa_pairs[:n]

# Quiz logic
if st.button(labels["start_quiz"]) or st.session_state.quiz_started:
    if not st.session_state.quiz_started:
        context = get_summary(st.session_state.selected_topic)
        ai_questions = generate_ai_questions(context, n=st.session_state.num_questions)

        questions = []
        for qa in ai_questions:
            options = [qa['answer']]
            while len(options) < 4:
                distractor = random.choice(TOPICS)
                if distractor != qa['answer'] and distractor not in options:
                    options.append(distractor)
            random.shuffle(options)
            questions.append({
                "question": qa['question'],
                "answer": qa['answer'],
                "options": options
            })

        st.session_state.question_bank = questions
        st.session_state.score = 0
        st.session_state.current_q = 0
        st.session_state.quiz_started = True

    q_index = st.session_state.current_q
    questions = st.session_state.question_bank

    if q_index < len(questions):
        q = questions[q_index]

        st.markdown("---")
        col1, col2 = st.columns(2)
        col1.metric("📊 Score", st.session_state.score)
        col2.metric("🔢 Question", f"{q_index + 1} / {len(questions)}")
        st.progress((q_index + 1) / len(questions))

        st.markdown(f"### {labels['question']} {q_index + 1}")
        st.markdown(f"💡 *{labels['desc']}*")
        st.write(q["question"])

        selected = st.radio("🔘 Choose your answer:", q["options"], key=q_index)

        if st.button(labels["submit"], key=f"submit_{q_index}"):
            if selected == q["answer"]:
                st.success(labels["correct"])
                st.session_state.score += 1
            else:
                st.error(f"{labels['incorrect']} *{q['answer']}*")
            st.session_state.current_q += 1
            st.rerun()

    else:
        st.balloons()
        st.success(f"{labels['completed']} *{st.session_state.score} / {len(questions)}*")
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(labels["restart"]):
                st.session_state.quiz_started = False
                st.session_state.question_bank = []
                st.session_state.current_q = 0
                st.session_state.score = 0
                st.rerun()
        with col2:
            st.markdown(f"[\ud83d\udcd8 Learn more on Wikipedia](https://en.wikipedia.org/wiki/{st.session_state.selected_topic})")
