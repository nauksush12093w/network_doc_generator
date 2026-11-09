from models import Host, Service, NetworkConfig, Criticality, Connection


def convert_dict_to_network(data: dict) -> NetworkConfig:
    """
    Превращает проверенный словарь в объекты вашей модели.
    """
    network = NetworkConfig()

    # 1. Обрабатываем узлы (хосты)
    for node in data.get("nodes", []):
        # Превращаем строку в Enum ("high" -> "High" -> Criticality.HIGH)
        crit_str = node["criticality"].capitalize()
        crit_enum = Criticality(crit_str)

        # Создаем хост со всеми полями
        host = Host(
            name=node.get("name", node["id"]), # Красивое имя (если нет, берем ID)
            ip_address=node.get("ip_address", "0.0.0.0"),
            os=node.get("type", "Unknown"),
            criticality=crit_enum,
            node_id=node["id"],                # Сохраняем ID
            node_type=node.get("type", "host") # Сохраняем тип
        )
        
        network.hosts.append(host)

    # 2. Обрабатываем связи
    for conn_data in data.get("connections", []):
        source_id, target_id = conn_data
        
        connection = Connection(
            source=source_id,
            target=target_id,
            connection_type="Network"
        )
        network.connections.append(connection)

    return network