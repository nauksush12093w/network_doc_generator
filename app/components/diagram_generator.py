# участник 5
from pathlib import Path

from .processing.models import NetworkConfig


COLORS = {
    "low": "#E2F0D9",
    "medium": "#FFF2CC",
    "high": "#FCE4D6",
    "critical": "#F4CCCC",
}
IMPORTANT = {"high", "critical"}
TITLES = {
    "hosts": "Схема сети по узлам",
    "services": "Схема сети по сервисам",
    "critical": "Схема сети по критичности",
}


def _value(value, default=""):
    value = getattr(value, "value", value)
    if value is None:
        return default
    return str(value).strip() or default


def _level(value):
    level = _value(value, "low").lower()
    return level if level in COLORS else "low"


def _text(value):
    return " ".join(_value(value).split()).replace("\\", "\\\\").replace('"', '\\"')


def _host_key(host):
    key = _value(host.node_id) or _value(host.name)
    if not key:
        raise ValueError("У узла должно быть имя или node_id.")
    return key


def _host_label(host):
    parts = [_text(host.name or "Без названия")]
    if host.ip_address and host.ip_address != "0.0.0.0":
        parts.append(_text(host.ip_address))
    parts.append(f"Критичность: {_level(host.criticality).upper()}")
    return r"\n".join(parts)


def _service_label(service):
    parts = [_text(service.name or "Без названия")]
    if service.port:
        parts.append(f"Порт: {service.port}/{_text(service.protocol).upper()}")
    parts.append(f"Критичность: {_level(service.criticality).upper()}")
    return r"\n".join(parts)


def _node_type(host):
    node_type = _value(host.node_type, "host").lower()
    return {"network": "cloud", "database": "database"}.get(node_type, "node")


def _host_aliases(network):
    aliases = {}
    for index, host in enumerate(network.hosts):
        key = _host_key(host)
        if key in aliases:
            raise ValueError(f"Повторяющийся идентификатор узла: {key}.")
        aliases[key] = f"host_{index}"

    for connection in network.connections:
        if connection.source not in aliases or connection.target not in aliases:
            raise ValueError("Связь ссылается на узел, которого нет в сети.")

    return aliases


def _connections(network, aliases, included=None):
    result = []
    for connection in network.connections:
        if included is not None and (
            connection.source not in included or connection.target not in included
        ):
            continue
        line = f"{aliases[connection.source]} --> {aliases[connection.target]}"
        if connection.connection_type != "Network":
            line += f" : {_text(connection.connection_type)}"
        result.append(line)
    return result


def generate_plantuml(network: NetworkConfig, profile="hosts") -> str:
    """Создаёт диаграмму PlantUML: hosts, services или critical."""
    if not isinstance(network, NetworkConfig):
        raise TypeError("Нужно передать объект NetworkConfig.")
    if profile not in {"hosts", "services", "critical"}:
        raise ValueError("Профиль должен быть hosts, services или critical.")

    aliases = _host_aliases(network)
    lines = ["@startuml", f"title {TITLES[profile]}", "left to right direction", ""]

    if profile == "hosts":
        for host in network.hosts:
            alias = aliases[_host_key(host)]
            level = _level(host.criticality)
            lines.append(
                f'{_node_type(host)} "{_host_label(host)}" as {alias} {COLORS[level]}'
            )
        if not network.hosts:
            lines.append('rectangle "В описании сети нет узлов"')
        lines.extend([""] + _connections(network, aliases))

    elif profile == "services":
        for host in network.hosts:
            alias = aliases[_host_key(host)]
            level = _level(host.criticality)
            lines.append(
                f'package "{_host_label(host)}" as {alias} {COLORS[level]} {{'
            )
            if host.services:
                for index, service in enumerate(host.services):
                    service_level = _level(service.criticality)
                    lines.append(
                        f'  component "{_service_label(service)}" '
                        f'as service_{alias}_{index} {COLORS[service_level]}'
                    )
            else:
                lines.append('  rectangle "Сервисы не указаны"')
            lines.append("}")
        if not network.hosts:
            lines.append('rectangle "В описании сети нет узлов"')
        lines.extend([""] + _connections(network, aliases))

    else:
        selected = [
            host for host in network.hosts
            if _level(host.criticality) in IMPORTANT
            or any(_level(service.criticality) in IMPORTANT for service in host.services)
        ]
        selected_keys = {_host_key(host) for host in selected}

        for host in selected:
            alias = aliases[_host_key(host)]
            level = _level(host.criticality)
            lines.append(
                f'{_node_type(host)} "{_host_label(host)}" as {alias} {COLORS[level]}'
            )
            important_services = [
                service for service in host.services
                if _level(service.criticality) in IMPORTANT
            ]
            if important_services:
                lines.extend([f"note right of {alias}", "Важные сервисы:"])
                lines.extend(
                    f"{_text(service.name)} ({_level(service.criticality).upper()})"
                    for service in important_services
                )
                lines.append("end note")

        if not selected:
            lines.append('rectangle "Нет узлов с критичностью HIGH/CRITICAL"')
        lines.extend([""] + _connections(network, aliases, selected_keys))

    lines.extend(["", "@enduml", ""])
    return "\n".join(lines)


def write_plantuml_file(source: str, output_path: str | Path) -> Path:
    """Сохраняет исходный код диаграммы в файл .puml."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path
