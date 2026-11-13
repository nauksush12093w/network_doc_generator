# участник 5
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Literal

from .processing.models import Criticality, NetworkConfig

DiagramProfile = Literal["hosts", "services", "critical"]

PROFILE_TITLES = {
    "hosts": "Схема сети по узлам",
    "services": "Схема сети по сервисам",
    "critical": "Схема сети по критичности",
}

CRITICALITY_COLORS = {
    "low": "#E2F0D9",
    "medium": "#FFF2CC",
    "high": "#FCE4D6",
    "critical": "#F4CCCC",
}
IMPORTANT_LEVELS = {"high", "critical"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _value(value: object, default: str = "") -> str:
    """Возвращает строковое значение Enum или обычного поля."""
    if value is None:
        return default
    raw = getattr(value, "value", value)
    result = str(raw).strip()
    return result or default


def _criticality(value: object) -> str:
    level = _value(value, "low").lower()
    return level if level in CRITICALITY_COLORS else "low"


def _escape_label(value: object) -> str:
    """Безопасно подготавливает пользовательский текст для PlantUML.

    Переводы строк удаляются, чтобы содержимое имени/сервиса не могло
    добавить новую команду PlantUML. Переносы в наших подписях добавляются
    отдельно через ``\\n``.
    """
    text = _value(value)
    text = " ".join(text.splitlines())
    text = " ".join(text.split())
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _multiline(*parts: object) -> str:
    clean_parts = [_escape_label(part) for part in parts if _value(part)]
    return r"\n".join(clean_parts)


def _host_key(host: object) -> str:
    node_id = _value(getattr(host, "node_id", ""))
    name = _value(getattr(host, "name", ""))
    key = node_id or name
    if not key:
        raise ValueError("У каждого узла должно быть задано имя или node_id.")
    return key


def _host_alias(index: int) -> str:
    return f"host_{index}"


def _host_keyword(host: object) -> str:
    node_type = _value(getattr(host, "node_type", "host")).lower()
    if node_type == "network":
        return "cloud"
    if node_type == "database":
        return "database"
    return "node"


def _host_label(host: object) -> str:
    name = _value(getattr(host, "name", "Без названия"), "Без названия")
    ip = _value(getattr(host, "ip_address", ""))
    level = _criticality(getattr(host, "criticality", Criticality.LOW))
    parts = [name]
    if ip and ip != "0.0.0.0":
        parts.append(ip)
    parts.append(f"Критичность: {level.upper()}")
    return _multiline(*parts)


def _service_label(service: object) -> str:
    name = _value(getattr(service, "name", "Без названия"), "Без названия")
    port = _value(getattr(service, "port", ""))
    protocol = _value(getattr(service, "protocol", "TCP"), "TCP").upper()
    level = _criticality(getattr(service, "criticality", Criticality.LOW))
    details = [name]
    if port:
        details.append(f"Порт: {port}/{protocol}")
    details.append(f"Критичность: {level.upper()}")
    return _multiline(*details)


def _build_host_index(network: NetworkConfig) -> tuple[dict[str, str], dict[str, object]]:
    """Создаёт соответствие ключ узла -> alias PlantUML и проверяет связи."""
    aliases: dict[str, str] = {}
    hosts_by_key: dict[str, object] = {}

    for index, host in enumerate(network.hosts):
        key = _host_key(host)
        if key in aliases:
            raise ValueError(f"Обнаружен повторяющийся идентификатор узла: '{key}'.")
        aliases[key] = _host_alias(index)
        hosts_by_key[key] = host

    for connection in network.connections:
        source = _value(getattr(connection, "source", ""))
        target = _value(getattr(connection, "target", ""))
        if source not in aliases:
            raise ValueError(f"Связь ссылается на неизвестный исходный узел: '{source}'.")
        if target not in aliases:
            raise ValueError(f"Связь ссылается на неизвестный целевой узел: '{target}'.")

    return aliases, hosts_by_key


def _connection_lines(
    network: NetworkConfig,
    aliases: dict[str, str],
    included_keys: set[str] | None = None,
) -> list[str]:
    lines: list[str] = []
    for connection in network.connections:
        source = _value(getattr(connection, "source", ""))
        target = _value(getattr(connection, "target", ""))
        if included_keys is not None and (source not in included_keys or target not in included_keys):
            continue
        connection_type = _value(getattr(connection, "connection_type", "Network"), "Network")
        suffix = f" : {_escape_label(connection_type)}" if connection_type.lower() != "network" else ""
        lines.append(f"{aliases[source]} --> {aliases[target]}{suffix}")
    return lines


def _header(profile: DiagramProfile) -> list[str]:
    return [
        "@startuml",
        f"title {_escape_label(PROFILE_TITLES[profile])}",
        "left to right direction",
        "skinparam backgroundColor #FFFFFF",
        "skinparam defaultFontName Arial",
        "skinparam defaultFontSize 13",
        "skinparam shadowing false",
        "skinparam ArrowColor #64748B",
        "skinparam linetype ortho",
        "",
    ]


def _selected_critical_hosts(network: NetworkConfig) -> list[object]:
    selected = []
    for host in network.hosts:
        host_level = _criticality(getattr(host, "criticality", Criticality.LOW))
        has_important_service = any(
            _criticality(getattr(service, "criticality", Criticality.LOW)) in IMPORTANT_LEVELS
            for service in getattr(host, "services", [])
        )
        if host_level in IMPORTANT_LEVELS or has_important_service:
            selected.append(host)
    return selected


def generate_plantuml(network: NetworkConfig, profile: DiagramProfile = "hosts") -> str:
    """Строит исходный код PlantUML для выбранного профиля.

    Args:
        network: объект NetworkConfig после загрузки, проверки и преобразования.
        profile: ``hosts`` (все узлы), ``services`` (сервисы внутри узлов),
            либо ``critical`` (узлы с уровнем HIGH/CRITICAL или такими сервисами).

    Returns:
        Полный текст PlantUML, который можно сохранить в файл ``.puml``.

    Raises:
        TypeError: если вместо NetworkConfig передан другой тип.
        ValueError: если профиль неизвестен или связи ссылаются на отсутствующие узлы.
    """
    if not isinstance(network, NetworkConfig):
        raise TypeError("network должен быть объектом NetworkConfig.")
    if profile not in PROFILE_TITLES:
        raise ValueError("Неизвестный профиль. Используйте: hosts, services или critical.")

    aliases, _ = _build_host_index(network)
    lines = _header(profile)

    if profile == "hosts":
        for index, host in enumerate(network.hosts):
            level = _criticality(getattr(host, "criticality", Criticality.LOW))
            color = CRITICALITY_COLORS[level]
            keyword = _host_keyword(host)
            lines.append(f'{keyword} "{_host_label(host)}" as {_host_alias(index)} {color}')
        if not network.hosts:
            lines.append('rectangle "В описании сети нет узлов" as empty_network #EEEEEE')
        lines.extend([""] + _connection_lines(network, aliases))

    elif profile == "services":
        for index, host in enumerate(network.hosts):
            host_alias = _host_alias(index)
            host_label = _host_label(host)
            host_level = _criticality(getattr(host, "criticality", Criticality.LOW))
            host_color = CRITICALITY_COLORS[host_level]
            lines.append(f'package "{host_label}" as {host_alias} {host_color} {{')

            services = list(getattr(host, "services", []))
            if not services:
                empty_alias = f"empty_services_{index}"
                lines.append(f'  rectangle "Сервисы не указаны" as {empty_alias} #F3F4F6')
            else:
                for service_index, service in enumerate(services):
                    service_alias = f"service_{index}_{service_index}"
                    service_level = _criticality(getattr(service, "criticality", Criticality.LOW))
                    service_color = CRITICALITY_COLORS[service_level]
                    lines.append(
                        f'  component "{_service_label(service)}" as {service_alias} {service_color}'
                    )
            lines.append("}")

        if not network.hosts:
            lines.append('rectangle "В описании сети нет узлов" as empty_network #EEEEEE')
        lines.extend([""] + _connection_lines(network, aliases))

    else:  # profile == "critical"
        selected_hosts = _selected_critical_hosts(network)
        selected_keys = {_host_key(host) for host in selected_hosts}
        for host in selected_hosts:
            key = _host_key(host)
            alias = aliases[key]
            level = _criticality(getattr(host, "criticality", Criticality.LOW))
            lines.append(
                f'{_host_keyword(host)} "{_host_label(host)}" as {alias} {CRITICALITY_COLORS[level]}'
            )
            important_services = [
                service
                for service in getattr(host, "services", [])
                if _criticality(getattr(service, "criticality", Criticality.LOW)) in IMPORTANT_LEVELS
            ]
            if important_services:
                note_lines = ["note right of " + alias, "Важные сервисы:"]
                note_lines.extend(
                    f"{_escape_label(getattr(service, 'name', 'Без названия'))} "
                    f"({_criticality(getattr(service, 'criticality', Criticality.LOW)).upper()})"
                    for service in important_services
                )
                note_lines.append("end note")
                lines.extend(note_lines)

        if not selected_hosts:
            lines.append('rectangle "Нет узлов с критичностью HIGH/CRITICAL" as empty_critical #EEEEEE')
        lines.extend([""] + _connection_lines(network, aliases, selected_keys))

    lines.extend(["", "@enduml", ""])
    return "\n".join(lines)


def write_plantuml_file(plantuml_source: str, output_path: str | Path) -> Path:
    """Сохраняет PlantUML-текст в UTF-8 файл и возвращает путь."""
    if not isinstance(plantuml_source, str) or "@startuml" not in plantuml_source or "@enduml" not in plantuml_source:
        raise ValueError("Передан некорректный исходный код PlantUML.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plantuml_source, encoding="utf-8")
    return path


def render_plantuml_to_png(
    plantuml_source: str,
    output_path: str | Path,
    *,
    plantuml_jar: str | Path | None = None,
    timeout: int = 60,
) -> Path:
    """Преобразует PlantUML в PNG через локальный PlantUML CLI или JAR.

    Для запуска через JAR требуется Java и файл plantuml.jar. Путь к JAR
    можно передать аргументом или задать переменной окружения PLANTUML_JAR.
    Если PlantUML установлен как команда, используется исполняемый файл
    ``plantuml``. Внешние сетевые сервисы не используются.
    """
    if not isinstance(plantuml_source, str) or "@startuml" not in plantuml_source or "@enduml" not in plantuml_source:
        raise ValueError("Передан некорректный исходный код PlantUML.")
    if timeout <= 0:
        raise ValueError("timeout должен быть положительным числом.")

    jar_value = plantuml_jar or os.environ.get("PLANTUML_JAR")
    if jar_value:
        jar_path = Path(jar_value).expanduser()
        if not jar_path.is_file():
            raise FileNotFoundError(f"Файл PlantUML JAR не найден: {jar_path}")
        java = shutil.which("java")
        if not java:
            raise RuntimeError("Для запуска PlantUML JAR необходимо установить Java.")
        command = [java, "-Djava.awt.headless=true", "-jar", str(jar_path), "-tpng", "-pipe"]
    else:
        executable = shutil.which("plantuml")
        if not executable:
            raise RuntimeError(
                "Не найден PlantUML. Установите PlantUML CLI или задайте путь к plantuml.jar "
                "через аргумент plantuml_jar либо переменную PLANTUML_JAR."
            )
        command = [executable, "-tpng", "-pipe"]

    try:
        completed = subprocess.run(
            command,
            input=plantuml_source.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"PlantUML не завершил генерацию за {timeout} секунд.") from error

    if completed.returncode != 0:
        error_text = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Ошибка генерации PNG в PlantUML: {error_text or 'неизвестная ошибка'}")
    if not completed.stdout.startswith(PNG_SIGNATURE):
        error_text = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            "PlantUML не вернул корректное PNG-изображение. "
            + (f"Сообщение: {error_text}" if error_text else "Проверьте синтаксис диаграммы и установку PlantUML.")
        )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(completed.stdout)
    return path


def generate_diagram_files(
    network: NetworkConfig,
    output_dir: str | Path,
    profile: DiagramProfile = "hosts",
    *,
    render_png: bool = False,
    plantuml_jar: str | Path | None = None,
    file_prefix: str = "network",
) -> dict[str, Path]:
    """Сохраняет ``.puml`` и, по запросу, ``.png`` в указанную папку.

    Возвращает словарь с ключами ``plantuml`` и (если запрошен) ``png``.
    """
    if profile not in PROFILE_TITLES:
        raise ValueError("Неизвестный профиль. Используйте: hosts, services или critical.")

    safe_prefix = re.sub(r"[^A-Za-z0-9_-]+", "_", str(file_prefix)).strip("_-") or "network"
    directory = Path(output_dir)
    source = generate_plantuml(network, profile)
    puml_path = write_plantuml_file(source, directory / f"{safe_prefix}_{profile}.puml")
    result = {"plantuml": puml_path}

    if render_png:
        png_path = render_plantuml_to_png(
            source,
            directory / f"{safe_prefix}_{profile}.png",
            plantuml_jar=plantuml_jar,
        )
        result["png"] = png_path

    return result
