import os
import uuid
import shutil
from flask import Flask, request, jsonify, send_from_directory, redirect, url_for

app = Flask(__name__)

# Укажите путь к сетевой папке
NETWORK_FOLDER = r"\\home\share"
os.makedirs(NETWORK_FOLDER, exist_ok=True)

# Функция для создания уникальной подпапки
def create_unique_folder():
    unique_id = str(uuid.uuid4())
    folder_path = os.path.join(NETWORK_FOLDER, unique_id)
    os.makedirs(folder_path, exist_ok=True)
    return unique_id, folder_path

# Главная страница с формой загрузки
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>File Server</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <div class="container mt-5 p-4 border rounded shadow bg-white">
                <h1 class="text-center mb-4">Загрузить файлы</h1>
                <form method="POST" enctype="multipart/form-data" class="mb-4" id="uploadForm">
                    <input type="file" id="fileInput" name="files[]" class="form-control mb-3" multiple required>
                    
                    <!-- Список выбранных файлов -->
                    <ul id="fileList" class="list-group mb-3"></ul>
                    
                    <div class="d-flex justify-content-between">
                        <button type="button" class="btn btn-secondary" onclick="clearFiles()">Очистить выбор</button>
                        <button type="submit" class="btn btn-primary">Загрузить</button>
                    </div>
                </form>
            </div>
            <script>
                const fileInput = document.getElementById("fileInput");
                const fileList = document.getElementById("fileList");
                let filesArray = [];

                // Обновление списка файлов
                fileInput.addEventListener("change", function () {
                    const newFiles = Array.from(fileInput.files); // Преобразуем FileList в массив
                    filesArray = [...filesArray, ...newFiles]; // Добавляем новые файлы

                    updateFileList(); // Перерисовываем список
                });

                // Функция обновления списка файлов
                function updateFileList() {
                    fileList.innerHTML = ""; // Очищаем текущий список

                    filesArray.forEach((file, index) => {
                        const listItem = document.createElement("li");
                        listItem.className = "list-group-item d-flex justify-content-between align-items-center";

                        // Добавляем название файла
                        listItem.textContent = file.name;

                        // Добавляем кнопку удаления файла
                        const removeButton = document.createElement("button");
                        removeButton.className = "btn btn-danger btn-sm";
                        removeButton.textContent = "Remove";
                        removeButton.onclick = () => removeFile(index); // Обработчик удаления
                        
                        listItem.appendChild(removeButton);
                        fileList.appendChild(listItem);
                    });

                    // Обновляем input files для отправки формы
                    const dataTransfer = new DataTransfer();
                    filesArray.forEach(file => dataTransfer.items.add(file));
                    fileInput.files = dataTransfer.files;
                }

                // Функция удаления файла из списка
                function removeFile(index) {
                    filesArray.splice(index, 1); // Удаляем файл из массива
                    updateFileList(); // Перерисовываем список
                }

                // Очистка выбора файлов
                function clearFiles() {
                    filesArray = [];
                    fileInput.value = ""; // Очищаем input
                    updateFileList(); // Перерисовываем список
                }
            </script>
        </body>
        </html>
        '''

    elif request.method == 'POST':
        # Обработка загрузки файлов
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files part'}), 400

        files = request.files.getlist('files[]')
        if not files:
            return jsonify({'error': 'No files selected'}), 400

        # Создаём уникальную папку
        unique_id, folder_path = create_unique_folder()

        # Сохраняем файлы в папке
        for file in files:
            file.save(os.path.join(folder_path, file.filename))

        # Создаём ZIP-архив
        zip_path = os.path.join(NETWORK_FOLDER, f"{unique_id}.zip")
        import zipfile
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, folder_path))

        # Удаляем исходные файлы и папку
        shutil.rmtree(folder_path)

        # Сохраняем ссылку для скачивания
        download_link = request.url_root + f'download/{unique_id}'

        # **ПЕРЕНАПРАВЛЯЕМ НА ОТДЕЛЬНУЮ СТРАНИЦУ С ССЫЛКОЙ**
        return redirect(url_for('success', link=download_link))

# Страница с успешной загрузкой
@app.route('/success')
def success():
    # **Если страница перезагружена – возвращаемся на главную**
    link = request.args.get('link')
    if not link:
        return redirect(url_for('index'))

    # Отображаем ссылку
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upload Successful</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5 p-4 border rounded shadow bg-white">
            <h1 class="text-success text-center">Файлы успешно загруженны</h1>
            <p class="text-center">Ссылка для скачивания:</p>
            <div class="input-group mb-3">
                <input type="text" id="downloadLink" value="{link}" class="form-control" readonly>
                <button class="btn btn-outline-primary" onclick="copyLink()">Скопировать ссылку</button>
            </div>
            <a href="/" class="btn btn-secondary w-100">Загрузить еще файлы</a>
        </div>
        <script>
            function copyLink() {{
                var copyText = document.getElementById("downloadLink");
                copyText.select();
                document.execCommand("copy");
                alert("Link copied to clipboard!");
            }}
        </script>
    </body>
    </html>
    '''

# Скачивание ZIP-архива
@app.route('/download/<unique_id>', methods=['GET'])
def download_files(unique_id):
    zip_path = os.path.join(NETWORK_FOLDER, f"{unique_id}.zip")
    if not os.path.exists(zip_path):
        return jsonify({'error': 'File not found'}), 404

    return send_from_directory(NETWORK_FOLDER, f"{unique_id}.zip", as_attachment=True)

