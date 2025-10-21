let currentIntervalId = null;
let currentReportId = null;

// ✅ Add this once, globally
document.addEventListener("DOMContentLoaded", () => {
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendMessageBtn");

  messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault(); // stop newline
      sendBtn.click(); // trigger send
    }
  });
});

document.addEventListener("click", async (e) => {
  const icon = e.target.closest('[data-lucide="message-circle"]');
  if (!icon) return;

  const row = icon.closest("tr");
  const reportId = row.dataset.id;
  const messageBox = document.getElementById("messageBox");
  const messageList = messageBox.querySelector(".message-list");
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendMessageBtn");
  const closeBtn = document.getElementById("closeMessageBox");

  // Skip if same chat already open
  if (messageBox.classList.contains("show") && currentReportId === reportId) return;

  // Stop previous refresh
  if (currentIntervalId) {
    clearInterval(currentIntervalId);
    currentIntervalId = null;
  }

  currentReportId = reportId;
  messageBox.querySelector(".message-header span").textContent =
    `Messages for Report ID - ${reportId}`;
  messageList.innerHTML = "";

  // Show the box
  messageBox.classList.remove("hidden");
  messageBox.classList.add("show");

  async function loadMessages() {
    if (currentReportId !== reportId || !messageBox.classList.contains("show")) return;

    try {
      const res = await fetch(`/reports/${reportId}/messages/`);
      const data = await res.json();

      if (data.error) {
        console.error(data.error);
        return;
      }

      messageList.innerHTML = "";
      data.messages.forEach((msg) => {
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("message", msg.is_self ? "sent" : "received");
        msgDiv.innerHTML = `
          ${!msg.is_self ? `<div class="avatar">${msg.sender[0]}</div>` : ""}
          <div class="bubble poppins-regular">
            ${msg.text}
            <span class="timestamp">${msg.timestamp}</span>
          </div>`;
        messageList.appendChild(msgDiv);
      });

      messageList.scrollTop = messageList.scrollHeight;
    } catch (error) {
      console.error("Error loading messages:", error);
    }
  }

  // Load immediately and start polling
  await loadMessages();
  currentIntervalId = setInterval(loadMessages, 5000);

  // Send message
  sendBtn.onclick = async () => {
    const text = messageInput.value.trim();
    if (!text) return;

    try {
      const res = await fetch(`/reports/${reportId}/messages/send/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      const msg = await res.json();
      if (res.ok) {
        messageInput.value = "";
        await loadMessages();
      } else {
        alert(msg.error || "Failed to send message");
      }
    } catch (error) {
      console.error("Error sending message:", error);
    }
  };

  // Handle close
  closeBtn.onclick = () => {
    if (currentIntervalId) {
      clearInterval(currentIntervalId);
      currentIntervalId = null;
    }
    messageBox.classList.remove("show");
    setTimeout(() => messageBox.classList.add("hidden"), 200);
    currentReportId = null;
  };
});
