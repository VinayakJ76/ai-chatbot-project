let currentConversationId = null;
let userId = "Guest";

document.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  checkSetup();
  loadConversations();

  // Listener for the custom model dropdown toggle
  const modelSelect = document.getElementById("model-select");
  if (modelSelect) {
    modelSelect.addEventListener("change", (e) => {
      const customInput = document.getElementById("custom-model");
      if (customInput) {
        // Safety check
        if (e.target.value === "custom") {
          customInput.style.display = "block";
        } else {
          customInput.style.display = "none";
        }
      }
    });
  }
});

// --- Sidebar Logic ---
function loadConversations() {
  fetch(`/api/conversations/${userId}`)
    .then((res) => res.json())
    .then((data) => {
      const list = document.getElementById("conv-list");
      list.innerHTML = "";
      if (userId === "Guest") {
        list.innerHTML =
          '<div style="padding:15px; text-align:center; color:#666; font-size:12px;">Login to save history</div>';
        return;
      }
      data.forEach((c) => {
        const div = document.createElement("div");
        div.className = `conv-item ${c.id === currentConversationId ? "active" : ""}`;
        div.innerText = c.title;
        div.onclick = () => loadChat(c.id);
        list.appendChild(div);
      });
    });
}

function startNewChat() {
  return fetch("/api/conversations/new", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  })
    .then((res) => res.json())
    .then((data) => {
      currentConversationId = data.conversation_id;
      document.getElementById("chatbox").innerHTML = "";
      closeSidebar();
    });
}

function loadChat(convId) {
  currentConversationId = convId;
  document.getElementById("chatbox").innerHTML =
    '<div class="message ai"><i>Loading...</i></div>';
  loadConversations();
  closeSidebar();

  fetch(`/api/history/${convId}`)
    .then((res) => res.json())
    .then((history) => {
      const chatbox = document.getElementById("chatbox");
      chatbox.innerHTML = "";
      history.forEach((msg) => {
        const className = msg.role === "user" ? "user" : "ai";
        const content =
          msg.role === "user" ? msg.content : marked.parse(msg.content);
        chatbox.innerHTML += `<div class="message ${className}">${content}</div>`;
      });
      chatbox.scrollTop = chatbox.scrollHeight;
    });
}

function toggleSidebar() {
  document.getElementById("sidebar").classList.toggle("open");
}
function closeSidebar() {
  document.getElementById("sidebar").classList.remove("open");
}

// --- Modals Logic ---
function openUserModal() {
  document.getElementById("user-modal").style.display = "block";
}
function closeUserModal() {
  document.getElementById("user-modal").style.display = "none";
}

function openSettingsModal() {
  document.getElementById("api-key").value =
    localStorage.getItem("apiKey") || "";

  const savedModel =
    localStorage.getItem("model") || "stepfun/step-3.5-flash:free";
  const select = document.getElementById("model-select");
  const customInput = document.getElementById("custom-model");

  let found = false;
  if (select) {
    for (let i = 0; i < select.options.length; i++) {
      if (select.options[i].value === savedModel) {
        select.value = savedModel;
        found = true;
        break;
      }
    }
  }

  if (!found && customInput) {
    select.value = "custom";
    customInput.value = savedModel;
    customInput.style.display = "block";
  } else if (customInput) {
    customInput.style.display = "none";
  }

  document.getElementById("settings-modal").style.display = "block";
}
function closeSettingsModal() {
  document.getElementById("settings-modal").style.display = "none";
}

// --- Chat Logic ---
async function sendMessage() {
  const input = document.getElementById("user-input");
  const text = input.value.trim();

  // Clear welcome message
  const welcomeDiv = document.querySelector(".welcome-state");
  if (welcomeDiv) welcomeDiv.remove();

  if (!currentConversationId) {
    await startNewChat();
  }

  const apiKey = localStorage.getItem("apiKey");
  let model = localStorage.getItem("model") || "stepfun/step-3.5-flash:free";
  const searchEnabled = document.getElementById("search-toggle").checked;

  if (!text) return;
  if (!apiKey) {
    openSettingsModal();
    return;
  }

  const chatbox = document.getElementById("chatbox");
  chatbox.innerHTML += `<div class="message user">${text}</div>`;
  input.value = "";
  chatbox.scrollTop = chatbox.scrollHeight;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        api_key: apiKey,
        user_id: userId,
        model: model,
        conversation_id: currentConversationId,
        use_search: searchEnabled,
      }),
    });
    const data = await response.json();
    if (response.ok) {
      const htmlContent = marked.parse(data.reply);
      chatbox.innerHTML += `<div class="message ai">${htmlContent}</div>`;
      if (userId !== "Guest") loadConversations();
    } else {
      chatbox.innerHTML += `<div class="message ai" style="color:red">Error: ${data.detail || "Unknown"}</div>`;
    }
    chatbox.scrollTop = chatbox.scrollHeight;
  } catch (error) {
    chatbox.innerHTML += `<div class="message ai" style="color:red">Error: ${error.message}</div>`;
  }
}

// --- Load/Save Logic ---
function loadSettings() {
  let savedUser = localStorage.getItem("userId") || "Guest";
  if (savedUser.includes("/") || savedUser.includes(":")) {
    savedUser = "Guest";
    localStorage.setItem("userId", "Guest");
  }
  userId = savedUser;
  document.getElementById("user-id").value =
    savedUser === "Guest" ? "" : savedUser;
  updateHeaderUsername();
}

function saveUser() {
  let uId = document.getElementById("user-id").value.trim();
  if (uId.includes("/") || uId.includes(":")) {
    alert("Invalid name.");
    return;
  }
  if (!uId) uId = "Guest";
  localStorage.setItem("userId", uId);
  userId = uId;
  updateHeaderUsername();
  closeUserModal();
  currentConversationId = null;
  document.getElementById("chatbox").innerHTML = "";
  loadConversations();
}

function saveSettings() {
  const apiKey = document.getElementById("api-key").value;
  let model = document.getElementById("model-select").value;
  if (model === "custom") {
    model = document.getElementById("custom-model").value;
  }

  localStorage.setItem("apiKey", apiKey);
  localStorage.setItem("model", model);
  closeSettingsModal();
}

function updateHeaderUsername() {
  document.getElementById("header-username").innerText =
    userId === "Guest" ? "Guest" : userId;
}
function checkSetup() {
  if (!localStorage.getItem("apiKey")) setTimeout(openSettingsModal, 500);
}

// Enter key listener
document.getElementById("user-input").addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});
