from datetime import datetime
import base64
import hashlib
import uuid

import streamlit as st
from openai import OpenAI

# Show title and description.
st.set_page_config(page_title="Chatbot", page_icon="💬", layout="wide")
st.markdown(
    """
    <style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  --app-bg: #0f1117;
  --panel-bg: #151923;
  --panel-border: #23283b;
  --text-primary: #f7f7f9;
  --text-muted: #a2a6b4;
  --accent: #2782d6;
}

/* Global app styling */
html, body, .stApp {
  background: var(--app-bg);
  color: var(--text-primary);
  font-family: "IBM Plex Sans", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}

/* Hide Streamlit chrome */
#MainMenu { visibility: hidden; }
footer { display: none; }
header { display: none; }

/* Main container */
div.block-container {
  padding-top: 2.5rem;
  max-width: 1100px;
}

/* App title */
.app-title {
  font-size: 1.3rem;
  letter-spacing: 0.08rem;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 1.5rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #111522 0%, #0b0d15 100%);
  border-right: 1px solid var(--panel-border);
}

/* Sidebar markdown width fix */
section[data-testid="stSidebar"] .stMarkdown {
  width: 100%;
}

/* Reduce spacing between sidebar buttons */
section[data-testid="stSidebar"] .stButton {
  margin-bottom: 0rem;
  gap: 0.5rem;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton button {
  width: 100%;
  background: var(--panel-bg);
  color: var(--text-primary);
  border: 1px solid var(--panel-bg);
  border-radius: 12px;
  padding: 0.35rem 0.6rem;

  /* LEFT ALIGN FIX */
  display: flex;
  justify-content: flex-start;
  align-items: center;
  text-align: left;
}

/* Inner button content alignment */
section[data-testid="stSidebar"] .stButton button > div {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  width: 100%;
}

/* Remove focus glow */
section[data-testid="stSidebar"] .stButton button:focus {
  box-shadow: none;
  outline: none;
}

/* Hover & active state */
section[data-testid="stSidebar"] .stButton button:hover,
section[data-testid="stSidebar"] .stButton button:active {
  background: var(--accent);
  color: #ffffff;
  border-color: var(--accent);
}

/* Activity cards */
.activity-card {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.6rem;
}

.activity-meta {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin-bottom: 0.35rem;
}

/* Dashboard cards */
.card {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: 16px;
  padding: 1rem 1.25rem;
}

.card h4 {
  margin: 0 0 0.6rem 0;
  font-size: 0.95rem;
  color: var(--text-muted);
}

.card-value {
  font-size: 1.6rem;
  font-weight: 600;
}

.subtle {
  color: var(--text-muted);
}
</style>

    """,
    unsafe_allow_html=True,
)
st.markdown('<div class="app-title">Branding Marketing Agency ChatGPT</div>', unsafe_allow_html=True)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def now_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

try:
    openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
except st.errors.StreamlitSecretNotFoundError:
    openai_api_key = ""

client = None
if openai_api_key:
    try:
        client = OpenAI(api_key=openai_api_key)
    except Exception:
        st.error("Could not initialize OpenAI client. Check your API key.")
        st.stop()
else:
    st.error("OpenAI API key is required. Add it to `.streamlit/secrets.toml`.")
    st.stop()

CHAT_MODELS = ["gpt-4o", "gpt-4o-mini"]

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

if "admin_view_user_id" not in st.session_state:
    st.session_state.admin_view_user_id = None

if "admin_section" not in st.session_state:
    st.session_state.admin_section = "Dashboard"

if "admin_user_id" not in st.session_state:
    admin_id = "admin@company.local"
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

def add_message(conversation: dict, role: str, content: str):
    conversation["messages"].append(
        {"role": role, "content": content, "created_at": now_timestamp()}
    )

def iter_all_messages():
    for user_id, conversations in st.session_state.user_conversations.items():
        user_name = st.session_state.users.get(user_id, {}).get("name", user_id)
        for conversation in conversations:
            for message in conversation["messages"]:
                yield {
                    "user_id": user_id,
                    "user_name": user_name,
                    "role": message.get("role", ""),
                    "content": message.get("content", ""),
                    "created_at": message.get("created_at", ""),
                }

def total_prompt_count() -> int:
    return sum(1 for message in iter_all_messages() if message["role"] == "user")

def total_message_chars() -> int:
    return sum(len(message["content"]) for message in iter_all_messages())

def build_week_series(total: int) -> list:
    base = max(total, 1)
    return [max(0, int(base * 0.08) + i * 3) for i in range(7)]

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
        login_user_id = st.text_input("Email")
        login_password = st.text_input("Password", type="password")
        login = st.form_submit_button("Sign in")
        if login:
            if authenticate(login_user_id, login_password):
                st.session_state.logged_in_user_id = login_user_id
                st.session_state.active_user_id = login_user_id
                ensure_user_conversations(login_user_id)
                st.success("Signed in.")
                st.rerun()
            else:
                st.error("Invalid credentials.")
    st.info(
        "Admin default: email `admin@company.local` / password `admin123` (change after first login)."
    )
    st.stop()

logged_in_user = current_user()
is_admin = logged_in_user and logged_in_user.get("role") == "Admin"
ensure_user_conversations(logged_in_user["id"])
if not is_admin:
    st.session_state.view_mode = "chat"

if not is_admin:
    st.session_state.active_user_id = st.session_state.logged_in_user_id

if is_admin and st.session_state.view_mode == "dashboard":
    with st.sidebar:
        st.markdown("### Admin")

        nav_items = [
            ("Dashboard", "🏠 Dashboard"),
            ("Users", "👥 Users"),
            ("Add new User", "➕ Add new User"),
            ("Chat Usage", "💬 Chat Usage"),
            ("Tokens & Costs", "🪙 Tokens & Costs"),
            ("API Logs", "📄 API Logs"),
            ("Billing", "💳 Billing"),
            ("Settings", "⚙️ Settings"),
        ]

        for key, label in nav_items:
            is_active = st.session_state.admin_section == key
            if st.button(
                label,
                use_container_width=True,
                type="primary" if is_active else "secondary",
                key=f"admin_nav_{key}",
            ):
                st.session_state.admin_section = key
                st.rerun()

        st.markdown("---")
        st.caption(f"Signed in as {logged_in_user['name']} ({logged_in_user['id']})")
else:
    st.sidebar.markdown("### Chats")
    if st.sidebar.button("➕ New chat", use_container_width=True):
        new_id = str(uuid.uuid4())[:8]
        conversations = st.session_state.user_conversations[st.session_state.logged_in_user_id]
        conversations.insert(
            0,
            {
                "id": new_id,
                "title": "New chat",
                "messages": [],
                "created_at": now_timestamp(),
            },
        )
        st.session_state.active_conversation_by_user[st.session_state.logged_in_user_id] = new_id
        st.session_state.view_mode = "chat"

    st.sidebar.markdown("---")


if not (is_admin and st.session_state.view_mode == "dashboard"):
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] .chat-list .stButton button {
            background: transparent;
            border: 1px solid transparent;
            padding: 0.35rem 0.65rem;
            border-radius: 10px;
            width: 100%;
        }
        section[data-testid="stSidebar"] .chat-list .stButton button:hover {
            background: rgba(255, 255, 255, 0.08) !important;
            color: white !important;
            border-color: transparent !important;
        }
        section[data-testid="stSidebar"] .chat-list .stButton button[kind="primary"],
        section[data-testid="stSidebar"] .chat-list .stButton button[aria-pressed="true"],
        section[data-testid="stSidebar"] .chat-list [data-testid="baseButton-primary"] {
            background: rgba(255, 255, 255, 0.12) !important;
            color: white !important;
            border-color: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    active_user_id = st.session_state.logged_in_user_id
    st.session_state.active_user_id = active_user_id
    ensure_user_conversations(active_user_id)
    conversations = st.session_state.user_conversations[active_user_id]

    active_conversation_id = st.session_state.active_conversation_by_user.get(active_user_id)
    st.sidebar.markdown('<div class="chat-list">', unsafe_allow_html=True)
    for conv in conversations:
        title = conv["title"]
        if len(title) > 26:
            title = title[:26] + "…"
        is_active = conv["id"] == active_conversation_id
        if st.sidebar.button(
            f"📁 {title}",
            key=f"chat_select_{conv['id']}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.active_conversation_by_user[active_user_id] = conv["id"]
            st.session_state.view_mode = "chat"
            st.rerun()
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    if active_conversation_id:
        active_conversation = next(
            (conv for conv in conversations if conv["id"] == active_conversation_id), None
        )
        with st.sidebar.expander("Chat options", expanded=False):
            new_title = st.text_input(
                "Rename chat",
                value=active_conversation["title"] if active_conversation else "",
            )
            if st.button("Save name", use_container_width=True):
                if active_conversation and new_title.strip():
                    active_conversation["title"] = new_title.strip()
                    st.rerun()
            if st.button("Delete chat", use_container_width=True):
                if active_conversation:
                    conversations[:] = [
                        conv for conv in conversations if conv["id"] != active_conversation_id
                    ]
                    if not conversations:
                        new_id = str(uuid.uuid4())[:8]
                        conversations.append(
                            {
                                "id": new_id,
                                "title": "New chat",
                                "messages": [],
                                "created_at": now_timestamp(),
                            }
                        )
                        st.session_state.active_conversation_by_user[active_user_id] = new_id
                    else:
                        st.session_state.active_conversation_by_user[active_user_id] = conversations[0]["id"]
                    st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Signed in as {logged_in_user['name']}")
    st.sidebar.caption(f"{logged_in_user['id']}")
    st.sidebar.markdown('<div class="sidebar-actions">', unsafe_allow_html=True)
    if is_admin and st.sidebar.button("🧭 Open dashboard", use_container_width=True):
        st.session_state.view_mode = "dashboard"
        st.rerun()
    if st.sidebar.button("🚪 Sign out", use_container_width=True):
        st.session_state.logged_in_user_id = None
        st.session_state.active_user_id = None
        st.rerun()
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

if st.session_state.view_mode == "dashboard" and is_admin:
    top_left, top_right = st.columns([3, 2])
    with top_left:
        st.markdown("## Admin Dashboard")
        st.caption(f"Welcome back, {logged_in_user['name']}")
    with top_right:
        action_cols = st.columns(2)
        with action_cols[0]:
            if st.button("Back to chat", use_container_width=True):
                st.session_state.view_mode = "chat"
                st.rerun()
        with action_cols[1]:
            if st.button("Sign out", use_container_width=True):
                st.session_state.logged_in_user_id = None
                st.session_state.active_user_id = None
                st.rerun()

    non_admin_ids = [
        user_id
        for user_id, user in st.session_state.users.items()
        if user.get("role") != "Admin"
    ]

    if st.session_state.admin_section == "Dashboard":
        total_users = len(non_admin_ids)
        total_prompts = total_prompt_count()
        total_chars = total_message_chars()
        active_users = len(
            [user_id for user_id in non_admin_ids if user_message_count(user_id) > 0]
        )

        kpi_cols = st.columns(4)
        kpi_cols[0].markdown(
            f'<div class="card"><h4>Total users</h4><div class="card-value">{total_users}</div></div>',
            unsafe_allow_html=True,
        )
        kpi_cols[1].markdown(
            f'<div class="card"><h4>Active users</h4><div class="card-value">{active_users}</div></div>',
            unsafe_allow_html=True,
        )
        kpi_cols[2].markdown(
            f'<div class="card"><h4>Total prompts</h4><div class="card-value">{total_prompts}</div></div>',
            unsafe_allow_html=True,
        )
        kpi_cols[3].markdown(
            f'<div class="card"><h4>Estimated tokens</h4><div class="card-value">{total_chars // 4}</div></div>',
            unsafe_allow_html=True,
        )

        chart_left, chart_right = st.columns([2, 1])
        with chart_left:
            st.markdown("#### Weekly prompt volume")
            st.line_chart(build_week_series(total_prompts), height=220, use_container_width=True)
        with chart_right:
            st.markdown("#### Weekly active users")
            st.line_chart(build_week_series(active_users), height=220, use_container_width=True)

        st.markdown("#### Recent activity")
        activity_items = list(iter_all_messages())
        activity_items = sorted(
            activity_items, key=lambda item: item.get("created_at") or "", reverse=True
        )[:6]
        if activity_items:
            for item in activity_items:
                role_label = "User" if item["role"] == "user" else "Assistant"
                content_preview = item["content"][:120]
                st.markdown(
                    f"""
                    <div class="activity-card">
                        <div class="activity-meta">{item['user_name']} · {role_label} · {item.get('created_at', '—') or '—'}</div>
                        <div>{content_preview}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.write("No activity yet.")

        st.markdown("#### Recent prompts")
        recent_prompts = [
            message["content"]
            for message in list(iter_all_messages())
            if message["role"] == "user"
        ][-6:]
        if recent_prompts:
            for prompt in reversed(recent_prompts):
                st.write(f"- {prompt}")
        else:
            st.write("No prompts yet.")

    elif st.session_state.admin_section == "Users":
        st.subheader("Users")
        if not non_admin_ids:
            st.info("No users created yet.")
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

    elif st.session_state.admin_section == "Add new User":
        st.subheader("Add new user")
        with st.form("create_user_form_main", clear_on_submit=True):
            new_name = st.text_input("Name")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Add user")
            if submitted:
                email_value = new_email.strip().lower()
                if not new_name.strip() or not new_password.strip() or not email_value:
                    st.warning("Please provide a name, email, and password to create a user.")
                elif email_value in st.session_state.users:
                    st.warning("That email is already in use. Please choose another.")
                else:
                    created_at = now_timestamp()
                    st.session_state.users[email_value] = {
                        "id": email_value,
                        "name": new_name.strip(),
                        "email": email_value,
                        "role": "Member",
                        "status": "Active",
                        "created_at": created_at,
                        "last_active": created_at,
                        "message_count": 0,
                        "password_hash": hash_password(new_password.strip()),
                    }
                    st.session_state.user_conversations[email_value] = [
                        {
                            "id": "welcome",
                            "title": "New chat",
                            "messages": [],
                            "created_at": created_at,
                        }
                    ]
                    st.session_state.active_conversation_by_user[email_value] = "welcome"
                    st.success(
                        f"User created. Email (ID): `{email_value}` | Temp password: `{new_password.strip()}`"
                    )

    elif st.session_state.admin_section == "Chat Usage":
        st.subheader("Chat Usage")
        if non_admin_ids:
            user_labels = {
                f"{st.session_state.users[user_id]['name']} ({user_id})": user_id
                for user_id in non_admin_ids
            }
            selected_label = st.selectbox(
                "Select user",
                options=list(user_labels.keys()),
                index=list(user_labels.values()).index(st.session_state.admin_view_user_id)
                if st.session_state.admin_view_user_id in user_labels.values()
                else 0,
            )
            st.session_state.admin_view_user_id = user_labels[selected_label]
            view_user_id = st.session_state.admin_view_user_id

            recent_prompts = []
            for conversation in st.session_state.user_conversations.get(view_user_id, []):
                recent_prompts.extend(
                    msg["content"] for msg in conversation["messages"] if msg["role"] == "user"
                )
            st.markdown("#### Recent prompts")
            if recent_prompts:
                for prompt in reversed(recent_prompts[-10:]):
                    st.write(f"- {prompt}")
            else:
                st.write("No prompts yet.")
        else:
            st.info("No users available.")

    elif st.session_state.admin_section == "Tokens & Costs":
        st.subheader("Tokens & Costs")
        total_chars = total_message_chars()
        estimated_tokens = total_chars // 4
        estimated_cost = estimated_tokens * 0.000002
        token_cols = st.columns(3)
        token_cols[0].markdown(
            f'<div class="card"><h4>Estimated tokens</h4><div class="card-value">{estimated_tokens}</div></div>',
            unsafe_allow_html=True,
        )
        token_cols[1].markdown(
            f'<div class="card"><h4>Estimated cost</h4><div class="card-value">${estimated_cost:,.4f}</div></div>',
            unsafe_allow_html=True,
        )
        token_cols[2].markdown(
            f'<div class="card"><h4>Prompt volume</h4><div class="card-value">{total_prompt_count()}</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("#### Weekly token usage")
        st.line_chart(build_week_series(estimated_tokens), height=220, use_container_width=True)

    elif st.session_state.admin_section == "API Logs":
        st.subheader("API Logs")
        logs = []
        for message in list(iter_all_messages())[-12:]:
            logs.append(
                {
                    "role": message["role"],
                    "content": message["content"][:80] + ("..." if len(message["content"]) > 80 else ""),
                }
            )
        if logs:
            st.dataframe(logs, use_container_width=True, hide_index=True)
        else:
            st.write("No logs yet.")

    elif st.session_state.admin_section == "Billing":
        st.subheader("Billing")
        st.markdown(
            '<div class="card"><h4>Plan</h4><div class="card-value">Starter</div><div class="subtle">No active billing method</div></div>',
            unsafe_allow_html=True,
        )

    elif st.session_state.admin_section == "Settings":
        st.subheader("Settings")
        st.markdown(
            '<div class="card"><h4>Workspace</h4><div class="card-value">Branding Marketing Agency</div><div class="subtle">Admin only</div></div>',
            unsafe_allow_html=True,
        )
else:
    conversation = get_active_conversation(active_user_id)
    if not conversation:
        st.info("Create a new chat to start chatting.")
    else:
        selected_model = st.selectbox("Model", CHAT_MODELS, index=0)
        st.markdown(
            f"**Chatting as** {st.session_state.users[active_user_id]['name']}"
            if is_admin
            else ""
        )
        for message in conversation["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Message ChatGPT (use /image for images)"):
            add_message(conversation, "user", prompt)
            with st.chat_message("user"):
                st.markdown(prompt)

            if conversation["title"] == "New chat":
                conversation["title"] = (
                    prompt[:42] + "..." if len(prompt) > 45 else prompt
                )

            if prompt.strip().lower().startswith("/image"):
                image_prompt = prompt.replace("/image", "", 1).strip()
                if not image_prompt:
                    st.warning("Add a prompt after /image to generate an image.")
                else:
                    try:
                        image = client.images.generate(
                            model="gpt-image-1",
                            prompt=image_prompt,
                            size="1024x1024",
                        )
                        image_b64 = image.data[0].b64_json
                        image_bytes = base64.b64decode(image_b64)
                        with st.chat_message("assistant"):
                            st.image(image_bytes, caption=image_prompt, use_container_width=True)
                        add_message(conversation, "assistant", "[image]")
                    except Exception as exc:
                        with st.chat_message("assistant"):
                            st.error(f"Image generation failed: {exc}")
                        add_message(conversation, "assistant", "[image generation failed]")
            else:
                stream = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in conversation["messages"]
                    ],
                    stream=True,
                )

                with st.chat_message("assistant"):
                    response = st.write_stream(stream)
                add_message(conversation, "assistant", response)

            st.session_state.users[active_user_id]["message_count"] = user_message_count(
                active_user_id
            )
            st.session_state.users[active_user_id]["last_active"] = now_timestamp()
