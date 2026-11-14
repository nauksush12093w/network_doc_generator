
from pathlib import Path

from app.components.data_loader import load_network_file
from app.components.processing.converter import convert_dict_to_network
from app.components.processing.processor import (
    process_by_hosts,
)
from app.components.diagram_generator import (
    generate_plantuml,
    write_plantuml_file,
    render_plantuml_to_png,
)


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"


def generate_network_diagram(file_path, profile="hosts"):
    """
    Основной процесс генерации сетевой диаграммы.
    """

    # 1. Загрузка и валидация
    data = load_network_file(file_path)

    # 2. Преобразование данных в NetworkConfig
    network = convert_dict_to_network(data)

    # 3. Подготовка статистики для интерфейса
    statistics = process_by_hosts(network)

    # 4. Генерация PlantUML
    plantuml_source = generate_plantuml(
        network,
        profile=profile
    )

    # 5. Сохранение PlantUML
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    puml_path = write_plantuml_file(
        plantuml_source,
        OUTPUT_DIR / "network.puml"
    )

    # 6. Генерация PNG
    png_path = render_plantuml_to_png(
        puml_path,
        output_dir=OUTPUT_DIR
    )

    # 7. Возврат результатов
    return {
        "statistics": statistics,
        "puml_path": str(puml_path),
        "png_path": str(png_path),
    }
