from models import Host, Service, NetworkConfig, Criticality, Connection


def create_sample_network() -> NetworkConfig:
    """Создает тестовую сеть для проверки обработки данных"""

    # 1. Веб-сервер (высокая критичность)
    web = Host(name="WebServer-01", ip_address="192.168.1.10", os="Ubuntu", criticality=Criticality.HIGH)
    web.services.append(Service(name="Nginx", port=80, criticality=Criticality.HIGH))
    web.services.append(Service(name="Node.js", port=3000, criticality=Criticality.HIGH))

    # 2. База данных (критичная)
    db = Host(name="DBServer-01", ip_address="192.168.1.20", os="CentOS", criticality=Criticality.CRITICAL)
    db.services.append(Service(name="PostgreSQL", port=5432, criticality=Criticality.CRITICAL))

    # 3. Резервный сервер (низкая критичность)
    backup = Host(name="BackupServer-01", ip_address="192.168.1.30", os="Debian", criticality=Criticality.LOW)
    backup.services.append(Service(name="Rsync", port=873, criticality=Criticality.LOW))

    # 4. Компьютер админа (средняя критичность)
    admin_pc = Host(name="AdminPC-01", ip_address="192.168.1.100", os="Windows 11", criticality=Criticality.MEDIUM)

    # Связи между ними
    connections = [
        Connection(source="WebServer-01", target="DBServer-01", connection_type="DB"),
        Connection(source="AdminPC-01", target="WebServer-01", connection_type="SSH"),
        Connection(source="BackupServer-01", target="DBServer-01", connection_type="Backup"),
    ]

    network = NetworkConfig()
    network.hosts.extend([web, db, backup, admin_pc])
    network.connections.extend(connections)
    return network