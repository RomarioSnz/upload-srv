// Получаем элементы управления
const toggleOptions = document.getElementById("toggleOptions");
const optionsContainer = document.getElementById("optionsContainer");
const uploadButton = document.getElementById("uploadButton");
const fileList = document.getElementById("fileList");
const progressContainer = document.getElementById("progressContainer");
const uploadProgressBar = document.getElementById("uploadProgressBar");
const statusText = document.getElementById("statusText");
const clearSelectionBtn = document.getElementById("clearSelectionBtn");

const zipProgressContainer = document.getElementById("zipProgressContainer");
const zipStatusText = document.getElementById("zipStatusText");
const zipProgressBar = document.getElementById("zipProgressBar");

let selectedFiles = [];

// Переключение отображения дополнительных опций
toggleOptions.addEventListener("click", () => {
  optionsContainer.classList.toggle("hidden");
});

// Обработчик выбора файлов
document.getElementById("selectFilesBtn").addEventListener("click", () => {
  const input = document.createElement("input");
  input.type = "file";
  input.multiple = true;
  input.onchange = () => handleFiles(input.files);
  input.click();
});

// Обработчик выбора папок
document.getElementById("selectFoldersBtn").addEventListener("click", () => {
  const input = document.createElement("input");
  input.type = "file";
  input.multiple = true;
  input.webkitdirectory = true;
  input.onchange = () => handleFiles(input.files, true);
  input.click();
});

// Функция обработки выбранных файлов
function handleFiles(files, isFolder = false) {
  Array.from(files).forEach(file => {
    const relativePath = isFolder ? (file.webkitRelativePath || file.name) : file.name;
    if (!selectedFiles.some(f => f.path === relativePath)) {
      selectedFiles.push({ file, path: relativePath });
    }
  });
  renderFileList();
  toggleUploadButton();
}

// Функция отображения списка выбранных файлов
function renderFileList() {
  if (selectedFiles.length === 0) {
    fileList.innerHTML = '<p class="text-center text-muted">Файлы не выбраны</p>';
  } else {
    fileList.innerHTML = selectedFiles.map((item, index) => `
      <div class="file-item">
        ${item.path}
        <button class="btn-delete" onclick="removeFile(${index})">🗑</button>
      </div>`).join("");
  }
}

// Функция удаления файла из списка
function removeFile(index) {
  selectedFiles.splice(index, 1);
  renderFileList();
  toggleUploadButton();
}

// Управление состоянием кнопок загрузки и очистки списка
function toggleUploadButton() {
  const hasFiles = selectedFiles.length > 0;
  uploadButton.disabled = !hasFiles;
  clearSelectionBtn.disabled = !hasFiles;
}

// Очистка списка файлов
clearSelectionBtn.addEventListener("click", () => {
  selectedFiles = [];
  renderFileList();
  toggleUploadButton();
});

// Загрузка файлов
uploadButton.addEventListener("click", () => {
  if (selectedFiles.length === 0) {
    alert("Выберите файлы!");
    return;
  }

  const formData = new FormData();
  selectedFiles.forEach(item => formData.append("files[]", item.file, item.path));

  const zipName = document.getElementById("zipName").value.trim();
  const password = document.getElementById("zipPassword").value.trim();
  if (zipName) formData.append("zip_name", zipName);
  if (password) formData.append("password", password);

  progressContainer.classList.remove("hidden");
  uploadProgressBar.style.width = "0%";

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/", true);

  // Отслеживание прогресса загрузки
  xhr.upload.onprogress = event => {
    if (event.lengthComputable) {
      const percentComplete = Math.round((event.loaded / event.total) * 100);
      uploadProgressBar.style.width = percentComplete + "%";
      uploadProgressBar.innerText = percentComplete + "%";
    }
  };

  xhr.onload = () => {
    if (xhr.status === 200) {
      const data = JSON.parse(xhr.responseText);
      if (data.task_id) checkTaskStatus(data.task_id);
    } else {
      alert("Ошибка загрузки файлов!");
    }
  };

  xhr.send(formData);
});

// Функция опроса статуса задачи упаковки архива
async function checkTaskStatus(taskId) {
  console.log("Начинаем отслеживание задачи:", taskId);
  zipProgressContainer.classList.remove("hidden");
  zipStatusText.innerText = "📦 Архив создаётся...";

  const pollStatus = async (attempts = 0) => {
    console.log(`Запрос статуса (попытка ${attempts + 1}): /status/${taskId}`);
    try {
      const response = await fetch(`/status/${taskId}`);
      const data = await response.json();
      console.log("Ответ от сервера:", data);

      if (data.state === "PROGRESS") {
        zipProgressBar.style.width = `${data.progress}%`;
        zipProgressBar.innerText = `${data.progress}%`;
        if (data.progress === 100) {
          zipStatusText.innerText = "✅ Файл загружен! Идёт упаковка архива...";
        }
        setTimeout(() => pollStatus(attempts), 2000);
      } else if (data.state === "SUCCESS") {
        console.log("Архив готов, редирект на скачивание:", data.link);
        zipStatusText.innerText = "🎉 Архив успешно создан! Перенаправляем...";
        setTimeout(() => {
          window.location.href = `/success?link=${encodeURIComponent(data.link)}`;
        }, 2000);
      } else if (data.state === "FAILURE") {
        zipStatusText.innerText = "⚠ Ошибка при обработке архива!";
        alert("Ошибка при обработке архива!");
      } else {
        console.error("Неизвестное состояние задачи:", data);
        zipStatusText.innerText = "⏳ Ожидание ответа сервера...";
        if (attempts < 10) {
          setTimeout(() => pollStatus(attempts + 1), 2000);
        } else {
          zipStatusText.innerText = "❌ Сервер не отвечает.";
          alert("Ошибка получения статуса задачи!");
        }
      }
    } catch (error) {
      console.error("Ошибка запроса статуса:", error);
      zipStatusText.innerText = "⏳ Ожидание ответа сервера...";
      if (attempts < 10) {
        setTimeout(() => pollStatus(attempts + 1), 2000);
      } else {
        zipStatusText.innerText = "❌ Сервер не отвечает.";
        alert("Ошибка получения статуса задачи!");
      }
    }
  };

  pollStatus();
}
