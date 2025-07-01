import streamlit as st
import requests
import random
from transformers import T5Tokenizer, T5ForConditionalGeneration, pipeline

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
        "desc": "Which topic is described below?",
        "submit": "✅ Submit Answer",
        "correct": "✅ Correct!",
        "incorrect": "❌ Incorrect! Correct answer:",
        "completed": "🎉 Quiz completed! Final Score:",
        "restart": "🔄 Restart",
        "choose_topic": "Choose a topic",
        "select_difficulty": "🔥 Select Difficulty"
    },
    "hi": {
        "welcome": "आपके स्मार्ट विकिपीडिया-आधारित क्विज़ साथी में आपका स्वागत है!",
        "start_quiz": "▶️ नया क्विज़ शुरू करें",
        "question": "प्रश्न",
        "desc": "नीचे किस विषय का वर्णन किया गया है?",
        "submit": "✅ उत्तर सबमिट करें",
        "correct": "✅ सही उत्तर!",
        "incorrect": "❌ गलत उत्तर! सही उत्तर:",
        "completed": "🎉 क्विज़ पूरा हुआ! अंतिम स्कोर:",
        "restart": "🔄 पुनः प्रारंभ करें",
        "choose_topic": "एक विषय चुनें",
        "select_difficulty": "🔥 कठिनाई स्तर चुनें"
    },
    "te": {
        "welcome": "మీ స్మార్ట్ వికీపీడియా ఆధారిత క్విజ్‌కు స్వాగతం!",
        "start_quiz": "▶️ కొత్త క్విజ్ ప్రారంభించండి",
        "question": "ప్రశ్న",
        "desc": "కింద పేర్కొన్నది ఏ అంశాన్ని సూచిస్తుంది?",
        "submit": "✅ సమాధానాన్ని సమర్పించండి",
        "correct": "✅ సరిగ్గా ఉంది!",
        "incorrect": "❌ తప్పు! సరైన సమాధానం:",
        "completed": "🎉 క్విజ్ పూర్తయింది! తుది స్కోరు:",
        "restart": "🔄 మళ్లీ ప్రారంభించండి",
        "choose_topic": "దయచేసి ఒక విషయం ఎంచుకోండి",
        "select_difficulty": "🔥 దయచేసి కష్టతరత ఎంచుకోండి"
    }
}

TOPICS = ["Science", "History", "Art", "Biology", "Geography", "Technology", "Mathematics", "Astronomy"]

# Initialize session state
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "score" not in st.session_state:
    st.session_state.score = 0
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "question_bank" not in st.session_state:
    st.session_state.question_bank = []
if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = ""
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "en"
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Medium"
if "num_questions" not in st.session_state:
    st.session_state.num_questions = 5

# Load question generation pipeline
@st.cache_resource
def load_qg_model():
    tokenizer = T5Tokenizer.from_pretrained("iarfmoose/t5-base-question-generator", use_fast=False)
    model = T5ForConditionalGeneration.from_pretrained("iarfmoose/t5-base-question-generator")
    return pipeline("text2text-generation", model=model, tokenizer=tokenizer)

qg_pipeline = load_qg_model()

# Page setup
st.set_page_config(page_title="WikiWhiz Quizipedia", layout="centered")

# Sidebar
lang_ui = st.sidebar.selectbox("🌐 Choose Language / भाषा / భాష", list(LANGUAGES.keys()))
lang = LANGUAGES[lang_ui]
labels = LABELS[lang]
st.session_state.selected_lang = lang

# Header
st.image("https://upload.wikimedia.org/wikipedia/commons/6/63/Wikipedia-logo.png", width=70)
st.markdown("<h1 style='text-align: center;'>🧠 WikiWhiz – Quizipedia</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'>{labels['welcome']}</p>", unsafe_allow_html=True)
st.markdown("---")

# Selection (Before Quiz Starts)
if not st.session_state.quiz_started:
    with st.container():
        st.session_state.difficulty = st.select_slider(
            f"🔥 {labels['select_difficulty']}",
            options=["Easy", "Medium", "Hard"],
            value="Medium"
        )
        selected_topic = st.selectbox(f"🎯 {labels['choose_topic']}", TOPICS)
        st.session_state.selected_topic = selected_topic

        num_questions = st.slider("📝 Number of Questions", min_value=5, max_value=20, value=5)
        st.session_state.num_questions = num_questions

# Wikipedia extract fetcher
def fetch_extract(topic):
    try:
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": topic,
                "origin": "*"
            }
        )
        pages = response.json().get("query", {}).get("pages", {})
        page = next(iter(pages.values()))
        return page.get("extract", "")
    except Exception:
        return ""

# Generate question bank using QG model
def generate_question_bank(base_topic, n=5, difficulty="Medium"):
    search_results = []
    try:
        search_term = base_topic
        if difficulty == "Easy":
            search_term += " basics"
        elif difficulty == "Hard":
            search_term += " advanced"

        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": search_term,
                "format": "json",
                "origin": "*"
            }
        )
        results = resp.json().get("query", {}).get("search", [])
        search_results = [res['title'] for res in results][:n * 3]
    except Exception:
        pass

    questions = []
    used_titles = set()
    for title in search_results:
        if len(questions) >= n or title in used_titles or title == base_topic:
            continue
        extract = fetch_extract(title)
        if extract and len(extract) > 100:
            if difficulty == "Hard" and len(extract) < 500:
                continue
            try:
                generated = qg_pipeline(f"generate question: {extract}", max_length=64, do_sample=False)[0]['generated_text']
            except Exception:
                continue

            wrong_choices = [t for t in TOPICS if t != title]
            options = random.sample(wrong_choices, 3) + [title]
            random.shuffle(options)

            questions.append({
                "question": generated,
                "answer": title,
                "options": options,
                "context": extract[:400] + "..."
            })
            used_titles.add(title)
    return questions

# Quiz UI Flow
if st.button(labels["start_quiz"]) or st.session_state.quiz_started:
    if not st.session_state.quiz_started:
        questions = generate_question_bank(
            st.session_state.selected_topic,
            n=st.session_state.num_questions,
            difficulty=st.session_state.difficulty
        )
        st.session_state.question_bank = questions
        st.session_state.score = 0
        st.session_state.current_q = 0
        st.session_state.quiz_started = True

    questions = st.session_state.question_bank
    q_index = st.session_state.current_q

    if q_index < len(questions):
        q = questions[q_index]

        st.markdown("---")
        col1, col2 = st.columns(2)
        col1.metric("📊 Score", st.session_state.score)
        col2.metric("🔢 Question", f"{q_index + 1} / {len(questions)}")
        st.progress((q_index + 1) / len(questions))

        st.markdown(f"### {labels['question']} {q_index + 1}")
        st.markdown(f"💡 *{q['question']}*")
        st.caption("📚 Based on Wikipedia context:")
        st.info(q["context"])

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
            st.markdown(f"[📘 Learn more on Wikipedia](https://en.wikipedia.org/wiki/{st.session_state.selected_topic})")

