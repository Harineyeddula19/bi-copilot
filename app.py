import streamlit as st
import plotly.express as px

from copilot.pipeline import ask
from copilot.insights import generate_insight
from copilot import history
from copilot.voice import transcribe

# Set to False when you deploy the app publicly, so visitors never share a history file.
PERSIST_HISTORY = False

st.set_page_config(page_title="HR BI Copilot", page_icon="📊", layout="wide")

# ----------------------------------------------------------------- styling
st.markdown("""
<style>
.stApp {
  background:
    radial-gradient(1100px 520px at 8% -8%, rgba(124,58,237,.30), transparent 60%),
    radial-gradient(900px 480px at 100% 0%, rgba(6,182,212,.22), transparent 55%),
    radial-gradient(800px 500px at 50% 110%, rgba(236,72,153,.14), transparent 60%),
    #0B1020;
}
.block-container { max-width: 1100px; padding-top: 1.4rem; }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #1E1B4B 0%, #312E81 48%, #0F172A 100%);
  border-right: 1px solid rgba(255,255,255,.08);
}
.hero {
  background: linear-gradient(120deg, #7C3AED 0%, #2563EB 52%, #06B6D4 100%);
  border-radius: 22px; padding: 1.7rem 2rem; margin-bottom: 1.1rem;
  box-shadow: 0 14px 40px rgba(37,99,235,.35);
}
.hero h1 { margin: 0; font-size: 2.1rem; color: #fff; letter-spacing: -0.5px; }
.hero p { margin: .45rem 0 0 0; color: rgba(255,255,255,.92); font-size: 1.02rem; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; margin: .4rem 0 1.2rem 0; }
.stat { border-radius: 16px; padding: .9rem 1rem; color: #fff; }
.stat .n { font-size: 1.55rem; font-weight: 700; line-height: 1.1; }
.stat .l { font-size: .85rem; opacity: .92; }
.s1 { background: linear-gradient(135deg, #8B5CF6, #6D28D9); }
.s2 { background: linear-gradient(135deg, #06B6D4, #0E7490); }
.s3 { background: linear-gradient(135deg, #F59E0B, #D97706); }
.s4 { background: linear-gradient(135deg, #10B981, #047857); }
.voice-tip {
  border: 1px dashed rgba(255,255,255,.28); border-radius: 14px;
  padding: .7rem 1rem; margin: .2rem 0 1rem 0; background: rgba(255,255,255,.04);
}
.section-title { font-weight: 600; margin: .6rem 0 .4rem 0; color: #C4B5FD; }
[data-testid="stChatMessage"] {
  background: rgba(255,255,255,.045); border: 1px solid rgba(255,255,255,.09);
  border-radius: 18px; padding: .9rem 1.1rem;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
  border-left: 4px solid #8B5CF6;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  border-left: 4px solid #06B6D4;
}
.stButton > button {
  border-radius: 12px; border: 1px solid rgba(255,255,255,.16); transition: all .15s ease;
}
.stButton > button:hover { transform: translateY(-2px); border-color: #8B5CF6; }
[data-testid="stBaseButton-primary"], button[kind="primary"] {
  background: linear-gradient(120deg, #8B5CF6, #2563EB); border: none; color: #fff;
}
[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

EXAMPLES = [
    "Which department has the highest attrition rate?",
    "Average monthly salary by job title",
    "Number of hires per year",
    "Attrition rate by overtime category",
    "Average satisfaction score by education level",
    "How many employees work remotely 100% of the time?",
]


# ------------------------------------------------------------------- state
def init_state():
    if "chats" not in st.session_state:
        st.session_state["chats"] = history.load_chats() if PERSIST_HISTORY else {}
        fresh = history.new_chat()
        st.session_state["chats"][fresh["id"]] = fresh
        st.session_state["active"] = fresh["id"]


def active_chat():
    return st.session_state["chats"][st.session_state["active"]]


def persist():
    if PERSIST_HISTORY:
        history.save_chats(st.session_state["chats"])


def start_new_chat():
    if not active_chat()["messages"]:       # already on an empty chat
        return
    fresh = history.new_chat()
    st.session_state["chats"][fresh["id"]] = fresh
    st.session_state["active"] = fresh["id"]


def open_chat(chat_id):
    st.session_state["active"] = chat_id


def delete_chat():
    chats = st.session_state["chats"]
    chats.pop(st.session_state["active"], None)
    fresh = history.new_chat()
    chats[fresh["id"]] = fresh
    st.session_state["active"] = fresh["id"]
    persist()


def clear_all():
    fresh = history.new_chat()
    st.session_state["chats"] = {fresh["id"]: fresh}
    st.session_state["active"] = fresh["id"]
    persist()


def set_pending(text):
    st.session_state["pending"] = text


def give_feedback(chat_id, idx, value):
    chat = st.session_state["chats"][chat_id]
    msg = chat["messages"][idx]

    # Store feedback only in the current Streamlit session.
    msg["feedback"] = value

    # Do not write questions or SQL to a shared log file.



# ----------------------------------------------------------------- sidebar
def render_sidebar():
    with st.sidebar:
        st.markdown("## 📊 HR Copilot")
        st.caption("Ask your data anything.")
        st.button("➕  New chat", type="primary", width="stretch", on_click=start_new_chat)
        st.markdown("##### 🕘 History")
        chats = sorted((c for c in st.session_state["chats"].values() if c["messages"]),
                       key=lambda c: c["created"], reverse=True)
        if not chats:
            st.caption("Your past questions will appear here.")
        for c in chats:
            is_active = c["id"] == st.session_state["active"]
            st.button("💬 " + c["title"], key=f"open_{c['id']}", width="stretch",
                      type="primary" if is_active else "secondary",
                      on_click=open_chat, args=(c["id"],))
        st.divider()
        if active_chat()["messages"]:
            st.button("🗑️ Delete this chat", width="stretch", on_click=delete_chat)
        with st.expander("⚙️ More"):
            if st.checkbox("I want to clear ALL history"):
                st.button("Clear all history", width="stretch", on_click=clear_all)
            st.caption("History is stored only on this computer." if PERSIST_HISTORY
                       else "History is kept only until you close this page.")


# ------------------------------------------------------------------ pieces
def render_hero():
    st.markdown("""
    <div class="hero">
      <h1>📊 HR BI Copilot</h1>
      <p>Ask questions about your workforce in plain English or by voice.
      The AI writes the SQL, a safety layer checks it, and a read-only database runs it.</p>
    </div>""", unsafe_allow_html=True)


def render_welcome():
    st.markdown("""
    <div class="stats">
      <div class="stat s1"><div class="n">100,000</div><div class="l">Employees</div></div>
      <div class="stat s2"><div class="n">9</div><div class="l">Departments</div></div>
      <div class="stat s3"><div class="n">6</div><div class="l">Linked tables</div></div>
      <div class="stat s4"><div class="n">Read-only</div><div class="l">Safe by design</div></div>
    </div>
    <div class="voice-tip">🎤 <b>Voice:</b> click the microphone in the box below, speak your
    question, then send it. Your words appear in the chat so you can check what was heard.</div>
    <div class="section-title">✨ Try one of these</div>
    """, unsafe_allow_html=True)
    cols = st.columns(3)
    for i, ex in enumerate(EXAMPLES):
        cols[i % 3].button(ex, key=f"ex_{i}", width="stretch",
                           on_click=set_pending, args=(ex,))


def make_chart(df, key):
    num = df.select_dtypes("number").columns
    cat = df.select_dtypes(exclude="number").columns
    if len(df) < 2 or len(num) < 1 or len(cat) < 1:
        return
    x, y = cat[0], num[0]
    if any(w in x.lower() for w in ("year", "month", "date")):
        fig = px.line(df, x=x, y=y, markers=True, color_discrete_sequence=["#22D3EE"])
    else:
        fig = px.bar(df, x=x, y=y, color=x,
                     color_discrete_sequence=px.colors.qualitative.Vivid)
        fig.update_layout(showlegend=False)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, width="stretch", key=key)


def render_answer(chat_id, idx, m):
    status = m["status"]
    if status == "declined":
        st.warning("I can't answer that from this data. "
                   + m["sql"].replace("CANNOT_ANSWER:", "Reason:"))
        return
    if status == "blocked":
        st.error(f"🛡️ Blocked for safety: {m['error']}")
        with st.expander("Show the blocked SQL"):
            st.code(m["sql"], language="sql")
        return
    if status == "api_error":
        st.error("The AI service had a problem. Wait a moment and try again.")
        with st.expander("Details"):
            st.code(m["error"])
        return
    if status == "error":
        st.error("I couldn't produce a working query. Try rephrasing the question.")
        with st.expander("Details"):
            st.code(m["sql"], language="sql")
            st.write(m["error"])
        return

    if m["retries"]:
        st.info("The first query failed, so it was corrected automatically.")
    df = history.unpack_df(m)
    if df.empty:
        st.warning("The query ran but returned no rows.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)
        if m["total_rows"] > len(df):
            st.caption(f"Showing the first {len(df)} of {m['total_rows']} rows.")
        make_chart(df, key=f"chart_{chat_id}_{idx}")
                # Generate a business insight from the actual SQL results
        chat = st.session_state["chats"][chat_id]

        question = (
            chat["messages"][idx - 1]["content"]
            if idx > 0
            else ""
        )

        insight = generate_insight(question, df)

        if insight:
            st.info("💡 Business Insight: " + insight)
    with st.expander("Show generated SQL"):
        st.code(m["sql"], language="sql")

    if m.get("feedback") is None:
        c1, c2, _ = st.columns([1, 1, 8])
        c1.button("👍", key=f"up_{chat_id}_{idx}", on_click=give_feedback, args=(chat_id, idx, 1))
        c2.button("👎", key=f"down_{chat_id}_{idx}", on_click=give_feedback, args=(chat_id, idx, 0))
    else:
        st.caption("Thanks for the feedback " + ("👍" if m["feedback"] == 1 else "👎"))


def render_message(chat, idx, m):
    if m["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(("🎤 " if m.get("voice") else "") + m["content"])
    else:
        with st.chat_message("assistant", avatar="🤖"):
            render_answer(chat["id"], idx, m)


def read_input(value):
    """Return (text, audio) from st.chat_input, which may be a string or a value object."""
    if value is None:
        return "", None
    if isinstance(value, str):
        return value, None
    return (getattr(value, "text", "") or ""), getattr(value, "audio", None)


def handle_question(chat, text, voice):
    chat["messages"].append({"role": "user", "content": text, "voice": voice})
    if chat["title"] == "New chat":
        chat["title"] = history.make_title(text)
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(("🎤 " if voice else "") + text)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            result = ask(text)
    chat["messages"].append(history.pack_result(result))
    persist()
    st.rerun()


# -------------------------------------------------------------------- main
init_state()
render_sidebar()
render_hero()

value = st.chat_input("Ask about your HR data, or tap the 🎤 to speak...", accept_audio=True)
text, audio = read_input(value)
voice = False
if value is not None and not text.strip() and audio is not None:
    with st.spinner("🎤 Listening..."):
        try:
            text = transcribe(audio)
            voice = True
        except Exception as e:
            st.error("I couldn't process the recording. Check your internet and try again.")
            with st.expander("Details"):
                st.code(str(e))
    if voice and not text:
        st.warning("I couldn't hear any words. Please try again and speak a little longer.")
question = (st.session_state.pop("pending", None) or text or "").strip()

chat = active_chat()
if not chat["messages"] and not question:
    render_welcome()
for i, m in enumerate(chat["messages"]):
    render_message(chat, i, m)
if question:
    handle_question(chat, question, voice)