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

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.pipeline import NetworkInputError, generate_network_diagram


main = Blueprint("main", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml", ".csv"}


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


@main.route("/api/generate", methods=["POST"])
def generate():
    uploaded_file = request.files.get("file")
    uploaded_connections = request.files.get("connections_file")

    if uploaded_file is None or not uploaded_file.filename:
        return jsonify({"error": "Файл не выбран"}), 400

    extension = Path(uploaded_file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Неподдерживаемый формат файла"}), 400

    profile = request.form.get("profile", "hosts")
    show_ports = request.form.get("labels", "true") == "true"
    criticality = request.form.get("criticality", "all")

    if criticality not in {"all", "high", "medium"}:
        return jsonify({"error": "Неизвестный уровень критичности"}), 400

    if profile not in {"hosts", "services", "critical"}:
        return jsonify({"error": "Неизвестный профиль"}), 400

    connections_filename = None

    if extension == ".csv":
        if uploaded_connections is None or not uploaded_connections.filename:
            return jsonify({
                "error": "Для CSV-файла необходимо также загрузить connections.csv"
            }), 400

        connections_extension = Path(
            uploaded_connections.filename
        ).suffix.lower()

        if connections_extension != ".csv":
            return jsonify({
                "error": "Файл соединений должен иметь формат CSV"
            }), 400

        connections_filename = "connections.csv"

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            safe_extension = extension
            filename = f"network{safe_extension}"

            file_path = temp_path / filename
            uploaded_file.save(file_path)

            connections_path = None

            if connections_filename and uploaded_connections is not None:
                connections_dir = temp_path / "connections"
                connections_dir.mkdir()

                connections_path = connections_dir / connections_filename
                uploaded_connections.save(connections_path)

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
            "png_url": url_for(
                "main.get_result",
                filename=Path(result["png_path"]).name
            ),
            "puml_url": url_for(
                "main.get_result",
                filename=Path(result["puml_path"]).name
            ),
        })

    except NetworkInputError as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 400

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 500

@main.route("/api/result/<filename>")
def get_result(filename):
    if not re.fullmatch(
        r"network(?:-[0-9a-f]{32})?\.(?:png|puml)",
        filename
    ):
        return jsonify({"error": "Недопустимое имя файла"}), 400

    return send_from_directory(OUTPUT_DIR, filename)
