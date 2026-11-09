
# Модуль загрузки сетевых данных из YAML, JSON и CSV.

import csv
import json
from pathlib import Path

import yaml

# Подключаем валидатор.
# Первый вариант используется при работе внутри пакета app.
# Второй позволяет запускать файл в отдельных тестах.
try:
    from .data_validator import validate_network
except ImportError:
    from data_validator import validate_network


def load_yaml(file_path):
    """
    Читает данные из YAML-файла.
    """

    try:
        with open(file_path, "r", encoding="utf-8-sig") as file:
            data = yaml.safe_load(file)

        return data

    except yaml.YAMLError as error:
        raise ValueError(
            f"Ошибка чтения YAML-файла: {error}"
        )

    except UnicodeDecodeError:
        raise ValueError(
            "Не удалось прочитать YAML: неверная кодировка."
        )

    except OSError as error:
        raise ValueError(
            f"Не удалось открыть YAML-файл: {error}"
        )


def load_json(file_path):
    """
    Читает данные из JSON-файла.
    """

    try:
        with open(file_path, "r", encoding="utf-8-sig") as file:
            data = json.load(file)

        return data

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Ошибка структуры JSON: строка {error.lineno}, "
            f"столбец {error.colno}."
        )

    except UnicodeDecodeError:
        raise ValueError(
            "Не удалось прочитать JSON: неверная кодировка."
        )

    except OSError as error:
        raise ValueError(
            f"Не удалось открыть JSON-файл: {error}"
        )


def load_csv(nodes_file, connections_file=None):
    """
    Читает CSV-файлы с узлами и соединениями.

    nodes_file — файл с информацией об устройствах.
    connections_file — файл с информацией о соединениях.
    """

    data = {
        "nodes": [],
        "connections": []
    }

    # Проверяем наличие необходимых столбцов узлов.
    required_node_columns = {
        "id",
        "name",
        "type",
        "criticality"
    }

    try:
        with open(
            nodes_file,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            if not reader.fieldnames:
                raise ValueError(
                    "CSV-файл узлов пуст или не содержит заголовков."
                )

            reader.fieldnames = [
                name.strip() for name in reader.fieldnames
            ]

            missing_columns = (
                required_node_columns - set(reader.fieldnames)
            )

            if missing_columns:
                raise ValueError(
                    "В network.csv отсутствуют столбцы: "
                    + ", ".join(sorted(missing_columns))
                )

            for row in reader:

                # Пропускаем полностью пустые строки.
                if not any(
                    value and value.strip()
                    for value in row.values()
                    if isinstance(value, str)
                ):
                    continue

                node = {
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "type": row.get("type"),
                    "criticality": row.get("criticality")
                }

                # IP-адрес добавляем только при его наличии.
                ip = row.get("ip_address")

                if ip and ip.strip():
                    node["ip_address"] = ip.strip()

                # Убираем лишние пробелы.
                for key, value in node.items():
                    if isinstance(value, str):
                        node[key] = value.strip()

                data["nodes"].append(node)

    except csv.Error as error:
        raise ValueError(
            f"Ошибка чтения CSV-файла узлов: {error}"
        )

    except UnicodeDecodeError:
        raise ValueError(
            "Не удалось прочитать CSV: неверная кодировка."
        )

    except OSError as error:
        raise ValueError(
            f"Не удалось открыть CSV-файл узлов: {error}"
        )

    # Если файл соединений не передан явно,
    # ищем connections.csv рядом с network.csv.
    if connections_file is None:

        possible_connections_file = (
            Path(nodes_file).parent / "connections.csv"
        )

        if possible_connections_file.exists():
            connections_file = possible_connections_file

    # Читаем соединения, если файл существует.
    if connections_file is not None:

        required_connection_columns = {
            "source",
            "target"
        }

        try:
            with open(
                connections_file,
                "r",
                encoding="utf-8-sig",
                newline=""
            ) as file:

                reader = csv.DictReader(file)

                if not reader.fieldnames:
                    raise ValueError(
                        "CSV-файл соединений пуст или не содержит заголовков."
                    )

                reader.fieldnames = [
                    name.strip() for name in reader.fieldnames
                ]

                missing_columns = (
                    required_connection_columns - set(reader.fieldnames)
                )

                if missing_columns:
                    raise ValueError(
                        "В connections.csv отсутствуют столбцы: "
                        + ", ".join(sorted(missing_columns))
                    )

                for row in reader:

                    source = row.get("source")
                    target = row.get("target")

                    if (
                        isinstance(source, str)
                        and isinstance(target, str)
                        and source.strip()
                        and target.strip()
                    ):
                        data["connections"].append([
                            source.strip(),
                            target.strip()
                        ])
                    else:
                        data["connections"].append([
                            source,
                            target
                        ])

        except csv.Error as error:
            raise ValueError(
                f"Ошибка чтения CSV-файла соединений: {error}"
            )

        except UnicodeDecodeError:
            raise ValueError(
                "Не удалось прочитать CSV соединений: неверная кодировка."
            )

        except OSError as error:
            raise ValueError(
                f"Не удалось открыть CSV-файл соединений: {error}"
            )

    return data


def load_network_file(file_path, connections_file=None):
    """
    Главная функция загрузчика.

    Определяет формат файла, читает данные
    и передает их на проверку.
    """

    file_path = Path(file_path)

    # Проверяем существование файла.
    if not file_path.exists():
        raise ValueError(
            f"Файл не найден: {file_path}"
        )

    # Проверяем, что это именно файл.
    if not file_path.is_file():
        raise ValueError(
            "Указанный путь не является файлом."
        )

    # Проверяем, что файл не пустой.
    if file_path.stat().st_size == 0:
        raise ValueError(
            "Загруженный файл пуст."
        )

    # Определяем формат по расширению.
    file_extension = file_path.suffix.lower()

    if file_extension == ".yaml" or file_extension == ".yml":
        data = load_yaml(file_path)

    elif file_extension == ".json":
        data = load_json(file_path)

    elif file_extension == ".csv":
        data = load_csv(file_path, connections_file)

    else:
        raise ValueError(
            f"Неподдерживаемый формат файла: {file_extension}"
        )

    # Проверяем корректность полученных данных.
    validate_network(data)

    # Возвращаем проверенную сетевую конфигурацию.
    return data
