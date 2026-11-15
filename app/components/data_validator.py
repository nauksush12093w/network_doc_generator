
from ipaddress import ip_address


ALLOWED_TYPES = {
    "network",
    "server",
    "database",
    "host",
    "device"
}

ALLOWED_CRITICALITY = {
    "low",
    "medium",
    "high",
    "critical"
}

ALLOWED_PROTOCOLS = {
    "TCP",
    "UDP"
}


def validate_structure(data):

    if not isinstance(data, dict):
        raise ValueError(
            "Данные должны иметь формат объекта."
        )

    if "nodes" not in data:
        raise ValueError(
            "Отсутствует обязательный раздел 'nodes'."
        )

    if "connections" not in data:
        raise ValueError(
            "Отсутствует обязательный раздел 'connections'."
        )

    if not isinstance(data["nodes"], list):
        raise ValueError(
            "Раздел 'nodes' должен быть списком."
        )

    if not isinstance(data["connections"], list):
        raise ValueError(
            "Раздел 'connections' должен быть списком."
        )


def validate_services(services, node_id):

    errors = []

    if not isinstance(services, list):
        return [
            f"Узел '{node_id}': раздел 'services' должен быть списком."
        ]

    for index, service in enumerate(services):

        service_number = index + 1

        if not isinstance(service, dict):
            errors.append(
                f"Узел '{node_id}', сервис №{service_number} "
                "должен быть объектом."
            )
            continue

        # Проверяем название
        name = service.get("name")

        if not isinstance(name, str) or not name.strip():
            errors.append(
                f"Узел '{node_id}', сервис №{service_number}: "
                "некорректное название."
            )

        # Проверяем порт
        port = service.get("port")

        if (
            not isinstance(port, int)
            or isinstance(port, bool)
            or not 1 <= port <= 65535
        ):
            errors.append(
                f"Узел '{node_id}', сервис №{service_number}: "
                "порт должен быть целым числом от 1 до 65535."
            )

        # Проверяем протокол
        protocol = service.get("protocol", "TCP")

        if (
            not isinstance(protocol, str)
            or protocol.upper() not in ALLOWED_PROTOCOLS
        ):
            errors.append(
                f"Узел '{node_id}', сервис №{service_number}: "
                "допустимые протоколы — TCP и UDP."
            )

        # Проверяем критичность сервиса
        criticality = service.get("criticality", "low")

        if (
            not isinstance(criticality, str)
            or criticality.lower() not in ALLOWED_CRITICALITY
        ):
            errors.append(
                f"Узел '{node_id}', сервис №{service_number}: "
                "некорректная критичность."
            )

    return errors


def validate_nodes(nodes):

    errors = []
    existing_ids = set()

    for index, node in enumerate(nodes):

        if not isinstance(node, dict):
            errors.append(
                f"Узел №{index + 1} должен быть объектом."
            )
            continue

        required_fields = [
            "id",
            "name",
            "type",
            "criticality"
        ]

        for field in required_fields:
            if field not in node:
                errors.append(
                    f"Узел №{index + 1}: отсутствует поле '{field}'."
                )

        if any(field not in node for field in required_fields):
            continue

        node_id = node["id"]

        if not isinstance(node_id, str) or not node_id.strip():
            errors.append(
                f"Узел №{index + 1}: ID должен быть непустой строкой."
            )
            continue

        if node_id in existing_ids:
            errors.append(
                f"Обнаружен повторяющийся ID: '{node_id}'."
            )
        else:
            existing_ids.add(node_id)

        if not isinstance(node["name"], str) or not node["name"].strip():
            errors.append(
                f"Узел '{node_id}': некорректное название."
            )

        if (
            not isinstance(node["type"], str)
            or node["type"].lower() not in ALLOWED_TYPES
        ):
            errors.append(
                f"Узел '{node_id}': неизвестный тип устройства."
            )

        if (
            not isinstance(node["criticality"], str)
            or node["criticality"].lower() not in ALLOWED_CRITICALITY
        ):
            errors.append(
                f"Узел '{node_id}': некорректная критичность."
            )

        # Проверяем IP-адрес
        ip = node.get("ip_address")

        if ip is not None:
            if not isinstance(ip, str):
                errors.append(
                    f"Узел '{node_id}': IP-адрес должен быть строкой."
                )
            else:
                try:
                    ip_address(ip)
                except ValueError:
                    errors.append(
                        f"Узел '{node_id}': неверный IP-адрес '{ip}'."
                    )

        # Проверяем сервисы узла
        if "services" in node:
            errors.extend(
                validate_services(node["services"], node_id)
            )

    return errors, existing_ids


def validate_connections(connections, existing_ids):

    errors = []

    for index, connection in enumerate(connections):

        if (
            not isinstance(connection, (list, tuple))
            or len(connection) != 2
        ):
            errors.append(
                f"Соединение №{index + 1} должно содержать "
                "два идентификатора."
            )
            continue

        source, target = connection

        if not isinstance(source, str) or not isinstance(target, str):
            errors.append(
                f"Соединение №{index + 1}: ID должны быть строками."
            )
            continue

        if not source.strip() or not target.strip():
            errors.append(
                f"Соединение №{index + 1}: ID не должны быть пустыми."
            )
            continue

        if source not in existing_ids:
            errors.append(
                f"Соединение №{index + 1}: "
                f"узел '{source}' не найден."
            )

        if target not in existing_ids:
            errors.append(
                f"Соединение №{index + 1}: "
                f"узел '{target}' не найден."
            )

    return errors


def validate_network(data):

    validate_structure(data)

    node_errors, existing_ids = validate_nodes(
        data["nodes"]
    )

    connection_errors = validate_connections(
        data["connections"],
        existing_ids
    )

    all_errors = node_errors + connection_errors

    if all_errors:
        error_message = "\n".join(
            f"- {error}" for error in all_errors
        )

        raise ValueError(
            "Обнаружены ошибки в сетевой конфигурации:\n"
            + error_message
        )

    return data
