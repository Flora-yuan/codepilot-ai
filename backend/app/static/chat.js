const questionInput = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");
const answerPanel = document.getElementById("answer");
const referencesList = document.getElementById("references");

sendButton.addEventListener("click", sendQuestion);
questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    sendQuestion();
  }
});

async function sendQuestion() {
  const question = questionInput.value.trim();
  if (!question) {
    showError("请输入问题。");
    return;
  }

  setLoading(true);
  answerPanel.textContent = "正在分析代码，请稍等...";
  referencesList.innerHTML = "";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "请求失败");
    }

    answerPanel.textContent = data.answer || "没有返回回答。";
    renderReferences(data.references || []);
  } catch (error) {
    showError(error.message || "请求出错，请稍后重试。");
  } finally {
    setLoading(false);
  }
}

function renderReferences(references) {
  referencesList.innerHTML = "";

  if (references.length === 0) {
    const item = document.createElement("li");
    item.textContent = "暂无引用代码位置。";
    referencesList.appendChild(item);
    return;
  }

  references.forEach((reference) => {
    const item = document.createElement("li");
    const filePath = reference.file_path || "unknown";
    const startLine = reference.start_line ?? "?";
    const endLine = reference.end_line ?? "?";
    item.textContent = `${filePath}:${startLine}-${endLine}`;
    referencesList.appendChild(item);
  });
}

function showError(message) {
  answerPanel.innerHTML = "";
  const errorText = document.createElement("p");
  errorText.className = "error";
  errorText.textContent = message;
  answerPanel.appendChild(errorText);
}

function setLoading(isLoading) {
  sendButton.disabled = isLoading;
  questionInput.disabled = isLoading;
  sendButton.textContent = isLoading ? "发送中" : "发送";
}
