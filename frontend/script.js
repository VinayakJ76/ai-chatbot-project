// Initialize on load
document.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  checkSetup();
});

// --- Settings Logic ---
function openSettings() {
  document.getElementById("settings-modal").style.display = "block";
}

function closeSettings() {
  document.getElementById("settings-modal").style.display = "none";
}

function loadSettings() {
  document.getElementById("api-key").value =
    localStorage.getItem("apiKey") || "";
  document.getElementById("user-id").value =
    localStorage.getItem("userId") || "";
  const savedModel =
    localStorage.getItem("model") || "stepfun/step-3.5-flash:free";

  // Handle dropdown
  const select = document.getElementById("model-select");
  const customInput = document.getElementById("custom-model");

  // Check if saved model is in standard dropdown
  let found = false;
  for (let i = 0; i < select.options.length; i++) {
    if (select.options[i].value === savedModel) found = true;
  }

  if (found) {
    select.value = savedModel;
  } else {
    select.value = "custom";
    customInput.value = savedModel;
    customInput.style.display = "block";
  }
}

function saveSettings() {
  const apiKey = document.getElementById("api-key").value;
  const userId = document.getElementById("user-id").value;
  let model = document.getElementById("model-select").value;

  if (model === "custom") {
    model = document.getElementById("custom-model").value;
  }

  if (!apiKey) {
    alert("Please enter an API Key");
    return;
  }

  localStorage.setItem("apiKey", apiKey);
  localStorage.setItem("userId", userId || "Guest");
  localStorage.setItem("model", model);

  closeSettings();
  checkSetup();
}

function checkSetup() {
  // If no key, force open settings
  if (!localStorage.getItem("apiKey")) {
    openSettings();
  }
}

// Toggle Custom Model Input
document.getElementById("model-select").addEventListener("change", (e) => {
  const customInput = document.getElementById("custom-model");
  if (e.target.value === "custom") {
    customInput.style.display = "block";
  } else {
    customInput.style.display = "none";
  }
});

// --- Chat Logic ---
async function sendMessage() {
  const input = document.getElementById("user-input");
  const chatbox = document.getElementById("chatbox");
  const text = input.value.trim();

  const apiKey = localStorage.getItem("apiKey");
  const userId = localStorage.getItem("userId");
  const model = localStorage.getItem("model");

  if (!text) return;
  if (!apiKey) {
    openSettings();
    return;
  }

  // UI Update
  chatbox.innerHTML += `<div class="message user">${text}</div>`;
  input.value = "";
  chatbox.scrollTop = chatbox.scrollHeight;

  // Add "Thinking..." indicator
  const loaderId = "loader-" + Date.now();
  chatbox.innerHTML += `<div class="message ai" id="${loaderId}"><i>Thinking...</i></div>`;
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
        use_search: true, // Enable search by default
      }),
    });

    const data = await response.json();

    // Remove loader
    document.getElementById(loaderId).remove();

    // RENDER MARKDOWN
    // We use marked.parse() to convert text to HTML
    const htmlContent = marked.parse(data.reply);

    chatbox.innerHTML += `<div class="message ai">${htmlContent}</div>`;
    chatbox.scrollTop = chatbox.scrollHeight;
  } catch (error) {
    document.getElementById(loaderId).remove();
    chatbox.innerHTML += `<div class="message ai" style="background:#ffdddd; color:#d8000c;">Error: ${error.message}</div>`;
  }
}

// Enter key listener
document
  .getElementById("user-input")
  .addEventListener("keypress", function (event) {
    if (event.key === "Enter") sendMessage();
  });
