(function () {
  const root = document.querySelector("[data-chat-root]");
  if (!root) return;

  const list = root.querySelector("[data-chat-list]");
  const form = root.querySelector("[data-chat-form]");
  const input = root.querySelector("[data-chat-input]");
  const status = root.querySelector("[data-chat-status]");
  const banner = document.querySelector("[data-chat-banner]");
  const notifDot = document.querySelector("[data-notif-dot]");

  const apiUrl = root.dataset.apiUrl;
  const currentUserId = Number(root.dataset.currentUserId || 0);
  const otherUserId = Number(root.dataset.otherUserId || 0);
  const pollMs = Number(root.dataset.pollMs || 3000);
  let lastMessageId = Number(root.dataset.lastMessageId || 0);
  let isFetching = false;
  let bannerTimer = null;
  let dotTimer = null;
  let highlightTimer = null;

  if (!apiUrl || !otherUserId || !list) return;

  function getCookie(name) {
    const cookie = document.cookie
      .split(";")
      .map((value) => value.trim())
      .find((value) => value.startsWith(`${name}=`));
    if (!cookie) return "";
    return decodeURIComponent(cookie.split("=")[1]);
  }

  function formatTimestamp(iso) {
    if (!iso) return "";
    const parsed = new Date(iso);
    if (Number.isNaN(parsed.getTime())) return "";
    return parsed.toLocaleString([], {
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function clearEmptyState() {
    const empty = list.querySelector(".chat-empty");
    if (empty) empty.remove();
  }

  function buildMessageElement(msg, isNew) {
    const row = document.createElement("div");
    const isMine = Number(msg.sender_id) === currentUserId;
    row.className = `chat-row ${isMine ? "chat-row--right" : "chat-row--left"}`;
    if (isNew) row.classList.add("chat-row--new");

    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${isMine ? "chat-bubble--me" : "chat-bubble--them"}`;

    const name = document.createElement("div");
    name.className = "chat-name";
    name.textContent = msg.sender_name || msg.sender_label || "User";

    const text = document.createElement("div");
    text.className = "chat-text";
    text.textContent = msg.content || "";

    const time = document.createElement("div");
    time.className = "chat-time";
    time.textContent = formatTimestamp(msg.timestamp);

    bubble.appendChild(name);
    bubble.appendChild(text);
    bubble.appendChild(time);
    row.appendChild(bubble);

    return row;
  }

  function scrollToBottom(smooth) {
    if (!list) return;
    if (smooth && typeof list.scrollTo === "function") {
      list.scrollTo({ top: list.scrollHeight, behavior: "smooth" });
    } else {
      list.scrollTop = list.scrollHeight;
    }
  }

  function showBanner(senderName) {
    if (!banner) return;
    const name = senderName || "New message";
    banner.textContent = `New message from ${name}`;
    banner.style.display = "block";
    banner.classList.remove("is-hiding");
    banner.classList.add("is-visible");

    if (bannerTimer) clearTimeout(bannerTimer);
    bannerTimer = setTimeout(() => {
      banner.classList.remove("is-visible");
      banner.classList.add("is-hiding");
      setTimeout(() => {
        banner.style.display = "none";
        banner.classList.remove("is-hiding");
      }, 220);
    }, 5000);
  }

  function activateNotifDot() {
    if (!notifDot) return;
    notifDot.classList.add("is-active");
    if (dotTimer) clearTimeout(dotTimer);
    dotTimer = setTimeout(() => {
      notifDot.classList.remove("is-active");
    }, 6000);
  }

  function highlightChat() {
    root.classList.add("chat-card--highlight");
    if (highlightTimer) clearTimeout(highlightTimer);
    highlightTimer = setTimeout(() => {
      root.classList.remove("chat-card--highlight");
    }, 1200);
  }

  function appendMessages(messages, isFromPoll) {
    if (!Array.isArray(messages) || messages.length === 0) return;
    clearEmptyState();

    let incomingName = "";
    let hasIncoming = false;

    for (const msg of messages) {
      if (msg.id && Number(msg.id) <= lastMessageId) {
        continue;
      }
      const isMine = Number(msg.sender_id) === currentUserId;
      const row = buildMessageElement(msg, Boolean(isFromPoll));
      list.appendChild(row);

      if (msg.id && Number(msg.id) > lastMessageId) {
        lastMessageId = Number(msg.id);
      }

      if (!isMine) {
        hasIncoming = true;
        incomingName = msg.sender_name || msg.sender_label || incomingName;
      }
    }

    scrollToBottom(true);

    if (hasIncoming && isFromPoll) {
      showBanner(incomingName);
      activateNotifDot();
      highlightChat();
    }
  }

  async function fetchMessages() {
    if (isFetching) return;
    isFetching = true;

    try {
      const url = `${apiUrl}?after_id=${encodeURIComponent(lastMessageId)}`;
      const resp = await fetch(url, { headers: { Accept: "application/json" } });
      if (!resp.ok) throw new Error("fetch failed");
      const payload = await resp.json();
      appendMessages(payload.messages || [], true);
    } catch (err) {
      if (status) status.textContent = "Unable to load messages.";
    } finally {
      isFetching = false;
      if (status && status.textContent === "Unable to load messages.") {
        setTimeout(() => {
          status.textContent = "";
        }, 1500);
      }
    }
  }

  async function sendMessage(text) {
    const trimmed = (text || "").trim();
    if (!trimmed) return;

    if (status) status.textContent = "Sending...";
    const sendButton = form ? form.querySelector("button[type='submit']") : null;
    if (sendButton) sendButton.disabled = true;

    try {
      const resp = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({
          receiver_id: otherUserId,
          content: trimmed,
        }),
      });

      if (!resp.ok) throw new Error("send failed");

      const payload = await resp.json();
      if (payload.message) appendMessages([payload.message], false);
      if (input) input.value = "";
      if (status) status.textContent = "";
    } catch (err) {
      if (status) status.textContent = "Message failed.";
      setTimeout(() => {
        if (status) status.textContent = "";
      }, 1500);
    } finally {
      if (sendButton) sendButton.disabled = false;
    }
  }

  if (form) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      sendMessage(input ? input.value : "");
    });
  }

  scrollToBottom(false);
  fetchMessages();
  setInterval(fetchMessages, pollMs);
})();
