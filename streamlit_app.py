from datetime import datetime
import hashlib
import uuid

import streamlit as st
from openai import OpenAI

# Show title and description.
st.set_page_config(page_title="Chatbot", page_icon="💬", layout="wide")
st.markdown(
    """
    <style>
    :root {
        --app-bg: #0f1117;
        --panel-bg: #151923;
        --panel-border: #23283b;
        --text-primary: #f7f7f9;
        --text-muted: #a2a6b4;
        --accent: #10a37f;
    }
    html, body, [class*="stApp"] {
        background: var(--app-bg);
        color: var(--text-primary);
        font-family: "IBM Plex Sans", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    }
    #MainMenu, footer { visibility: hidden; }
    .block-container { padding-top: 2.5rem; max-width: 1100px; }
    .app-title {
        font-size: 1.3rem;
        letter-spacing: 0.08rem;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 1.5rem;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111522 0%, #0b0d15 100%);
        border-right: 1px solid var(--panel-border);
    }
    section[data-testid="stSidebar"] .stButton button {
        width: 100%;
        background: var(--accent);
        color: white;
        border: 0;
    }
    .chat-shell {
        background: var(--panel-bg);
        border: 1px solid var(--panel-border);
        border-radius: 16px;
        padding: 1.5rem;
        min-height: 60vh;
    }
    .subtle { color: var(--text-muted); }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div class="app-title">Company ChatGPT</div>', unsafe_allow_html=True)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def now_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Demo response generator used when no API key is provided.
def generate_demo_response(prompt: str, history: list) -> str:
    # A simple canned/demo response generator. You can extend this to be richer.
    last_user = prompt
    context = " ".join(m["content"] for m in history[-6:]) if history else ""
    return (
        "[DEMO MODE] "
        f"I received your message: \"{last_user}\". "
        "This is a canned demo response — no external API was called."
        + (f" Context: {context}" if context else "")
    )

try:
    openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
except st.errors.StreamlitSecretNotFoundError:
    openai_api_key = ""

# Determine whether to run in demo mode or with a real OpenAI key.
demo_mode = False
client = None
demo_notice = ""
if openai_api_key:
    try:
        client = OpenAI(api_key=openai_api_key)
    except Exception:
        st.warning("Could not initialize OpenAI client; falling back to demo mode.")
        demo_mode = True
        demo_notice = "Demo mode is active (OpenAI client unavailable)."
else:
    demo_mode = True
    demo_notice = "Demo mode is active (no OpenAI API key provided)."

if "users" not in st.session_state:
    st.session_state.users = {}

if "user_conversations" not in st.session_state:
    st.session_state.user_conversations = {}

if "active_conversation_by_user" not in st.session_state:
    st.session_state.active_conversation_by_user = {}

if "active_user_id" not in st.session_state:
    st.session_state.active_user_id = None

if "logged_in_user_id" not in st.session_state:
    st.session_state.logged_in_user_id = None

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "chat"

if "admin_user_id" not in st.session_state:
    admin_id = "admin"
    st.session_state.users[admin_id] = {
        "id": admin_id,
        "name": "Admin",
        "email": "admin@company.local",
        "role": "Admin",
        "status": "Active",
        "created_at": now_timestamp(),
        "last_active": "—",
        "message_count": 0,
        "password_hash": hash_password("admin123"),
    }
    st.session_state.user_conversations[admin_id] = [
        {
            "id": "welcome",
            "title": "Welcome",
            "messages": [],
            "created_at": now_timestamp(),
        }
    ]
    st.session_state.active_conversation_by_user[admin_id] = "welcome"
    st.session_state.admin_user_id = admin_id

def authenticate(user_id: str, password: str) -> bool:
    user = st.session_state.users.get(user_id)
    if not user:
        return False
    return user.get("password_hash") == hash_password(password)

def current_user():
    return st.session_state.users.get(st.session_state.logged_in_user_id)

def ensure_user_conversations(user_id: str):
    if user_id not in st.session_state.user_conversations:
        conversation_id = str(uuid.uuid4())[:8]
        st.session_state.user_conversations[user_id] = [
            {
                "id": conversation_id,
                "title": "New chat",
                "messages": [],
                "created_at": now_timestamp(),
            }
        ]
        st.session_state.active_conversation_by_user[user_id] = conversation_id
    if user_id not in st.session_state.active_conversation_by_user:
        st.session_state.active_conversation_by_user[user_id] = (
            st.session_state.user_conversations[user_id][0]["id"]
        )

def get_active_conversation(user_id: str):
    conversations = st.session_state.user_conversations.get(user_id, [])
    active_id = st.session_state.active_conversation_by_user.get(user_id)
    for conversation in conversations:
        if conversation["id"] == active_id:
            return conversation
    return conversations[0] if conversations else None

def user_message_count(user_id: str) -> int:
    return sum(
        len(conversation["messages"])
        for conversation in st.session_state.user_conversations.get(user_id, [])
    )

if "user_messages" in st.session_state:
    for user_id, messages in st.session_state.user_messages.items():
        if user_id not in st.session_state.user_conversations:
            conversation_id = str(uuid.uuid4())[:8]
            st.session_state.user_conversations[user_id] = [
                {
                    "id": conversation_id,
                    "title": "Imported chat",
                    "messages": messages,
                    "created_at": now_timestamp(),
                }
            ]
            st.session_state.active_conversation_by_user[user_id] = conversation_id
    st.session_state.pop("user_messages", None)

if st.session_state.logged_in_user_id is None:
    st.subheader("Sign in")
    with st.form("login_form"):
        login_user_id = st.text_input("User ID")
        login_password = st.text_input("Password", type="password")
        login = st.form_submit_button("Sign in")
        if login:
            if authenticate(login_user_id, login_password):
                st.session_state.logged_in_user_id = login_user_id
                st.session_state.active_user_id = login_user_id
                ensure_user_conversations(login_user_id)
                st.success("Signed in.")
            else:
                st.error("Invalid credentials.")
    st.info("Admin default: user `admin` / password `admin123` (change after first login).")
    st.stop()

logged_in_user = current_user()
is_admin = logged_in_user and logged_in_user.get("role") == "Admin"
ensure_user_conversations(logged_in_user["id"])
if not is_admin:
    st.session_state.view_mode = "chat"

if is_admin and demo_notice:
    with st.sidebar:
        st.info(demo_notice)

st.sidebar.markdown("### Chats")
st.sidebar.caption(f"Signed in as {logged_in_user['name']} ({logged_in_user['id']})")
if st.sidebar.button("Sign out"):
    st.session_state.logged_in_user_id = None
    st.session_state.active_user_id = None
    st.experimental_rerun()

if not is_admin:
    st.session_state.active_user_id = st.session_state.logged_in_user_id

if is_admin:
    with st.sidebar.expander("Admin tools", expanded=False):
        if st.button("Open dashboard" if st.session_state.view_mode == "chat" else "Back to chat"):
            st.session_state.view_mode = (
                "dashboard" if st.session_state.view_mode == "chat" else "chat"
            )
        with st.form("create_user_form", clear_on_submit=True):
            st.markdown("**Create user**")
            new_name = st.text_input("Name")
            new_email = st.text_input("Email")
            new_password = st.text_input("Temporary password", type="password")
            submitted = st.form_submit_button("Add user")
            if submitted:
                if not new_name.strip() or not new_password.strip():
                    st.warning("Please provide a name and password to create a user.")
                else:
                    user_id = str(uuid.uuid4())[:8]
                    created_at = now_timestamp()
                    st.session_state.users[user_id] = {
                        "id": user_id,
                        "name": new_name.strip(),
                        "email": new_email.strip() if new_email.strip() else "—",
                        "role": "Member",
                        "status": "Active",
                        "created_at": created_at,
                        "last_active": created_at,
                        "message_count": 0,
                        "password_hash": hash_password(new_password.strip()),
                    }
                    st.session_state.user_conversations[user_id] = [
                        {
                            "id": "welcome",
                            "title": "New chat",
                            "messages": [],
                            "created_at": created_at,
                        }
                    ]
                    st.session_state.active_conversation_by_user[user_id] = "welcome"
                    st.session_state.active_user_id = user_id
                    st.success(
                        f"User created. ID: `{user_id}` | Temp password: `{new_password.strip()}`"
                    )

        user_options = {
            f"{user['name']} ({user_id})": user_id
            for user_id, user in st.session_state.users.items()
            if user.get("role") != "Admin"
        }
        if user_options:
            selected_label = st.selectbox(
                "Viewing user",
                options=list(user_options.keys()),
                index=list(user_options.values()).index(st.session_state.active_user_id)
                if st.session_state.active_user_id in user_options.values()
                else 0,
            )
            st.session_state.active_user_id = user_options[selected_label]
        else:
            st.info("Create a user to enable chat.")

active_user_id = st.session_state.active_user_id or st.session_state.logged_in_user_id
st.session_state.active_user_id = active_user_id
ensure_user_conversations(active_user_id)
conversations = st.session_state.user_conversations[active_user_id]

if st.sidebar.button("+ New chat"):
    new_id = str(uuid.uuid4())[:8]
    conversations.insert(
        0,
        {
            "id": new_id,
            "title": "New chat",
            "messages": [],
            "created_at": now_timestamp(),
        },
    )
    st.session_state.active_conversation_by_user[active_user_id] = new_id

conversation_labels = {
    f"{conv['title']} · {conv['id']}": conv["id"] for conv in conversations
}
active_conversation_id = st.session_state.active_conversation_by_user.get(active_user_id)
if conversation_labels:
    selected_conversation = st.sidebar.radio(
        "History",
        options=list(conversation_labels.keys()),
        index=list(conversation_labels.values()).index(active_conversation_id)
        if active_conversation_id in conversation_labels.values()
        else 0,
        label_visibility="collapsed",
    )
    st.session_state.active_conversation_by_user[active_user_id] = conversation_labels[
        selected_conversation
    ]

if st.session_state.view_mode == "dashboard" and is_admin:
    st.subheader("User Dashboard")
    user_count = len(st.session_state.users)
    total_messages = sum(
        user_message_count(user_id) for user_id in st.session_state.users.keys()
    )
    active_user_name = (
        st.session_state.users[st.session_state.active_user_id]["name"]
        if st.session_state.active_user_id in st.session_state.users
        else "—"
    )

    col_users, col_messages, col_active = st.columns(3)
    col_users.metric("Total users", user_count)
    col_messages.metric("Total messages", total_messages)
    col_active.metric("Active user", active_user_name)

    if user_count == 0:
        st.info("No users created yet. Use the sidebar to add users.")
    else:
        filtered_users = [
            {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "status": user["status"],
                "created_at": user["created_at"],
                "last_active": user["last_active"],
                "message_count": user_message_count(user["id"]),
            }
            for user in st.session_state.users.values()
            if user.get("role") != "Admin"
        ]
        st.dataframe(filtered_users, use_container_width=True, hide_index=True)

    if is_admin and st.session_state.active_user_id in st.session_state.user_conversations:
        st.subheader("Recent prompts (selected user)")
        recent_prompts = []
        for conversation in st.session_state.user_conversations[st.session_state.active_user_id]:
            recent_prompts.extend(
                msg["content"] for msg in conversation["messages"] if msg["role"] == "user"
            )
        recent_prompts = recent_prompts[-5:]
        if recent_prompts:
            for prompt in reversed(recent_prompts):
                st.write(f"- {prompt}")
        else:
            st.write("No prompts yet.")
else:
    conversation = get_active_conversation(active_user_id)
    if not conversation:
        st.info("Create a new chat to start chatting.")
    else:
        st.markdown(
            f"**Chatting as** {st.session_state.users[active_user_id]['name']}"
            if is_admin
            else ""
        )
        for message in conversation["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Message ChatGPT"):
            conversation["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            if conversation["title"] == "New chat":
                conversation["title"] = (
                    prompt[:42] + "..." if len(prompt) > 45 else prompt
                )

            if demo_mode or client is None:
                response = generate_demo_response(prompt, conversation["messages"])
                with st.chat_message("assistant"):
                    st.markdown(response)
                conversation["messages"].append({"role": "assistant", "content": response})
            else:
                stream = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in conversation["messages"]
                    ],
                    stream=True,
                )

                with st.chat_message("assistant"):
                    response = st.write_stream(stream)
                conversation["messages"].append({"role": "assistant", "content": response})

            st.session_state.users[active_user_id]["message_count"] = user_message_count(
                active_user_id
            )
            st.session_state.users[active_user_id]["last_active"] = now_timestamp()
