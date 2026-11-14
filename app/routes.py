from pathlib import Path
import tempfile

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    send_from_directory,
)
from werkzeug.utils import secure_filename

from app.pipeline import generate_network_diagram


main = Blueprint("main", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml", ".csv"}


# Страницы интерфейса

@main.route("/")
@main.route("/index.html")

def index():
    return render_template("index.html")


@main.route("/upload.html")
def upload():
    return render_template("upload.html")


@main.route("/settings.html")
def settings():
    return render_template("settings.html")


@main.route("/results.html")
def results():
    return render_template("results.html")


# Генерация диаграммы

@main.route("/api/generate", methods=["POST"])
def generate():
    uploaded_file = request.files.get("file")

    if uploaded_file is None:
        return jsonify({"error": "Файл не выбран"}), 400

    if not uploaded_file.filename:
        return jsonify({"error": "Файл не выбран"}), 400

    filename = secure_filename(uploaded_file.filename)
    extension = Path(filename).suffix.lower()

    if not filename or extension not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Неподдерживаемый формат файла"}), 400

    profile = request.form.get("profile", "hosts")

    if profile not in {"hosts", "services", "critical"}:
        return jsonify({"error": "Неизвестный профиль"}), 400

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / filename
            uploaded_file.save(file_path)

            result = generate_network_diagram(
                file_path,
                profile=profile
            )

        return jsonify({
            "success": True,
            "statistics": result["statistics"],
            "png_url": "/api/result/network.png",
            "puml_url": "/api/result/network.puml",
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# Получение готовых файлов

@main.route("/api/result/<filename>")
def get_result(filename):
    if filename not in {"network.png", "network.puml"}:
        return jsonify({"error": "Файл не найден"}), 404

    return send_from_directory(OUTPUT_DIR, filename)
