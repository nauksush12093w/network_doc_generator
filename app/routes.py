from pathlib import Path
import tempfile
import re

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    send_from_directory,
    url_for,
)

from app.pipeline import NetworkInputError, generate_network_diagram

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
    uploaded_connections = request.files.get("connections_file")

    if uploaded_file is None or not uploaded_file.filename:
        return jsonify({"error": "Файл не выбран"}), 400

    extension = Path(uploaded_file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Неподдерживаемый формат файла"}), 400

    filename = f"network{extension}"

    profile = request.form.get("profile", "hosts")
    show_ports = request.form.get("labels", "true") == "true"
    criticality = request.form.get("criticality", "all")

    if criticality not in {"all", "high", "medium"}:
        return jsonify({"error": "Неизвестный уровень критичности"}), 400
    

    if profile not in {"hosts", "services", "critical"}:
        return jsonify({"error": "Неизвестный профиль"}), 400

    # Для CSV дополнительно нужен файл с соединениями
    connections_filename = None

    if extension == ".csv":
        if uploaded_connections is None or not uploaded_connections.filename:
            return jsonify({
                "error": "Для CSV-файла необходимо также загрузить connections.csv"
            }), 400

        connections_extension = Path(uploaded_connections.filename).suffix.lower()

        if connections_extension != ".csv":
            return jsonify({
                "error": "Файл соединений должен иметь формат CSV"
            }), 400

        connections_filename = "connections.csv"
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Сохраняем основной файл
            file_path = temp_path / filename
            uploaded_file.save(file_path)

            # Сохраняем файл соединений, если он загружен
            connections_path = None

            if connections_filename:
                connections_dir = temp_path / "connections"
                connections_dir.mkdir()
                connections_path = connections_dir / connections_filename
                uploaded_connections.save(connections_path)

            # Запускаем обработку и генерацию диаграммы
            result = generate_network_diagram(
                file_path,
                profile=profile,
                connections_file=connections_path,
                show_ports=show_ports,
                criticality=criticality,
            )

        return jsonify({
            "success": True,
            "statistics": result["statistics"],
            "png_url": url_for("main.get_result", filename=Path(result["png_path"]).name),
            "puml_url": url_for("main.get_result", filename=Path(result["puml_path"]).name),
        })
    
    except NetworkInputError as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 400

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# Получение готовых файлов

@main.route("/api/result/<filename>")
def get_result(filename):
    if not re.fullmatch(r"network(?:-[0-9a-f]{32})?\.(?:png|puml)", filename):
        return jsonify({"error": "Файл не найден"}), 404

    return send_from_directory(OUTPUT_DIR, filename)
    if filename not in {"network.png", "network.puml"}:
        return jsonify({"error": "Файл не найден"}), 404

    return send_from_directory(OUTPUT_DIR, filename)
