from pathlib import Path

from app.components.data_loader import load_network_file
from app.components.processing.converter import convert_dict_to_network
from app.components.processing.processor import (
    process_by_hosts,
    process_by_criticality,
)
from app.components.diagram_generator import (
    generate_plantuml,
    write_plantuml_file,
    render_plantuml_to_png,
)


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"


def generate_network_diagram(
    file_path,
    profile="hosts",
    connections_file=None,
    show_ports=True,
    criticality="all",
):
    """
    Основной процесс генерации сетевой диаграммы.
    """

    # 1. Загрузка и валидация
    data = load_network_file(
        file_path,
        connections_file=connections_file
    )

    # 2. Преобразование данных в NetworkConfig
    network = convert_dict_to_network(data)
    allowed_levels = {
        "high": {"high", "critical"},
        "medium": {"medium", "high", "critical"},
    }

    if criticality in allowed_levels:
        levels = allowed_levels[criticality]
        network.hosts = [
            host
            for host in network.hosts
            if host.criticality.value.lower() in levels
        ]
        visible_ids = {host.node_id for host in network.hosts}
        network.connections = [
            connection
            for connection in network.connections
            if connection.source in visible_ids
            and connection.target in visible_ids
        ]

     # 3. Подготовка статистики для интерфейса
    if profile == "critical":
        statistics = process_by_criticality(network)
    else:
        statistics = process_by_hosts(network)

    # 4. Генерация PlantUML
    plantuml_source = generate_plantuml(
    network,
    profile=profile,
    show_ports=show_ports,
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
