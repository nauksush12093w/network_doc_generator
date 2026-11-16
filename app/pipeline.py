from pathlib import Path
from uuid import uuid4

from app.components.data_loader import load_network_file
from app.components.processing.converter import convert_dict_to_network
from app.components.processing.processor import (
    process_by_hosts,
    process_by_services,
    process_by_criticality,
)
from app.components.diagram_generator import (
    generate_plantuml,
    write_plantuml_file,
    render_plantuml_to_png,
)


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"


class NetworkInputError(ValueError):
    pass


def generate_network_diagram(
    file_path,
    profile="hosts",
    connections_file=None,
    show_ports=True,
    criticality="all",
):

    try:
        data = load_network_file(
            file_path,
            connections_file=connections_file,
        )
    except ValueError as error:
        raise NetworkInputError(str(error)) from error

    network = convert_dict_to_network(data)

    # Фильтрация по критичности узлов и сервисов
    allowed_levels = {
        "high": {"high", "critical"},
        "medium": {"medium", "high", "critical"},
    }

    if criticality in allowed_levels:
        levels = allowed_levels[criticality]

        network.hosts = [
            host
            for host in network.hosts
            if (
                host.criticality.value.lower() in levels
                or any(
                    service.criticality.value.lower() in levels
                    for service in host.services
                )
            )
        ]

        # Оставляем соединения только между видимыми узлами
        visible_ids = {host.node_id for host in network.hosts}

        network.connections = [
            connection
            for connection in network.connections
            if connection.source in visible_ids
            and connection.target in visible_ids
        ]

    # Выбор профиля обработки
    if profile == "critical":
        statistics = process_by_criticality(network)
    elif profile == "services":
        statistics = process_by_services(network)
    elif profile == "hosts":
        statistics = process_by_hosts(network)
    else:
        raise ValueError(f"Неизвестный профиль: {profile}")

    # Генерация PlantUML
    plantuml_source = generate_plantuml(
        network,
        profile=profile,
        show_ports=show_ports,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result_name = f"network-{uuid4().hex}"

    puml_path = write_plantuml_file(
        plantuml_source,
        OUTPUT_DIR / f"{result_name}.puml",
    )

    png_path = render_plantuml_to_png(
        puml_path,
        output_dir=OUTPUT_DIR,
    )

    return {
        "statistics": statistics,
        "puml_path": str(puml_path),
        "png_path": str(png_path),
    }
