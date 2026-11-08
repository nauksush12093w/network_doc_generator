
# Проверка корректности входных данных о сети.

from ipaddress import ip_address


# Допустимые типы сетевых устройств.
ALLOWED_TYPES = {
    "network",
    "server",
    "database",
    "host",
    "device"
}


# Допустимые уровни критичности.
ALLOWED_CRITICALITY = {
    "low",
    "medium",
    "high",
    "critical"
}


def validate_structure(data):
    """
    Проверяет общую структуру входных данных.
    """

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


def validate_nodes(nodes):
    """
    Проверяет каждый узел сети.
    """

    errors = []
    existing_ids = set()

    for index, node in enumerate(nodes):

        if not isinstance(node, dict):
            errors.append(
                f"Узел №{index + 1} должен быть объектом."
            )
            continue

        # Проверка обязательных полей.
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

        # Если нет обязательных полей, дальше проверять нечего.
        if any(field not in node for field in required_fields):
            continue

        node_id = node["id"]

        # Проверка идентификатора.
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

        # Проверка названия.
        if not isinstance(node["name"], str) or not node["name"].strip():
            errors.append(
                f"Узел '{node_id}': некорректное название."
            )

        # Проверка типа устройства.
        if (
            not isinstance(node["type"], str)
            or node["type"].lower() not in ALLOWED_TYPES
        ):
            errors.append(
                f"Узел '{node_id}': неизвестный тип устройства."
            )

        # Проверка критичности.
        if (
            not isinstance(node["criticality"], str)
            or node["criticality"].lower() not in ALLOWED_CRITICALITY
        ):
            errors.append(
                f"Узел '{node_id}': некорректная критичность."
            )

        # IP-адрес необязательный, но если он указан,
        # то должен быть корректным.
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

    return errors, existing_ids


def validate_connections(connections, existing_ids):
    """
    Проверяет соединения между узлами сети.
    """

    errors = []

    for index, connection in enumerate(connections):

        # Каждое соединение должно содержать два ID.
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

        # Проверяем, что ID являются строками.
        if not isinstance(source, str) or not isinstance(target, str):
            errors.append(
                f"Соединение №{index + 1}: ID должны быть строками."
            )
            continue

        # Проверяем существование первого узла.
        if source not in existing_ids:
            errors.append(
                f"Соединение №{index + 1}: "
                f"узел '{source}' не найден."
            )

        # Проверяем существование второго узла.
        if target not in existing_ids:
            errors.append(
                f"Соединение №{index + 1}: "
                f"узел '{target}' не найден."
            )

    return errors


def validate_network(data):
    """
    Главная функция проверки всей сетевой конфигурации.

    Если данные корректны, возвращает их.
    Если найдены ошибки, сообщает о них.
    """

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
