
            "list": "search",
            "srsearch": search_term,
            "format": "json",
            "origin": "*"
        })
        results = resp.json().get("query", {}).get("search", [])
        search_results = [res['title'] for res in results][:n*3]
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
            wrong_choices = [t for t in TOPICS if t != title]
            options = random.sample(wrong_choices, 3) + [title]
            random.shuffle(options)
            questions.append({
                "extract": extract[:400] + "...",
                "answer": title,
                "options": options
            })
            used_titles.add(title)
    return questions

# Quiz UI Flow
if st.button(labels["start_quiz"]) or st.session_state.quiz_started:
    if not st.session_state.quiz_started:
        questions = generate_question_bank(
            st.session_state.selected_topic,
            n=5,
            difficulty=st.session_state.difficulty
        )
        st.session_state.question_bank = questions
        st.session_state.score = 0
        st.session_state.current_q = 0
        st.session_state.quiz_started = True

    questions = st.session_state.question_bank
    q_index = st.session_state.current_q

    # Show quiz
    if q_index < len(questions):
        q = questions[q_index]

        st.markdown("---")
        col1, col2 = st.columns(2)
        col1.metric("📊 Score", st.session_state.score)
        col2.metric("🔢 Question", f"{q_index + 1} / {len(questions)}")
        st.progress((q_index + 1) / len(questions))

        st.markdown(f"### {labels['question']} {q_index + 1}")
        st.markdown(f"💡 *{labels['desc']}*")
        st.info(q["extract"])

        selected = st.radio("🔘 Choose your answer:", q["options"], key=q_index)

        if st.button(labels["submit"], key=f"submit_{q_index}"):
            if selected == q["answer"]:
                st.success(labels["correct"])
                st.session_state.score += 1
            else:
                st.error(f"{labels['incorrect']} *{q['answer']}*")
            st.session_state.current_q += 1
            st.rerun()

    # Quiz complete
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
