from app.components.processing.models import (
    Host, Service, NetworkConfig, Criticality, Connection
)

# 1. Создаем веб-сервер
web_server = Host(
    name="WebServer-01",
    ip_address="192.168.1.10",
    os="Ubuntu",
    criticality=Criticality.HIGH
)

web_server.services.append(
    Service(
        name="Nginx",
        port=80,
        criticality=Criticality.HIGH
    )
)

# 2. Создаем сервер БД
db_server = Host(
    name="DBServer-01",
    ip_address="192.168.1.20",
    os="CentOS",
    criticality=Criticality.CRITICAL
)

db_server.services.append(
    Service(
        name="PostgreSQL",
        port=5432,
        criticality=Criticality.CRITICAL
    )
)

# 3. Создаем связь
connection = Connection(
    source="WebServer-01",
    target="DBServer-01",
    connection_type="DB"
)

# 4. Собираем сеть
network = NetworkConfig()
network.hosts.append(web_server)
network.hosts.append(db_server)
network.connections.append(connection)

# 5. Выводим результат
print(f"Всего хостов: {len(network.hosts)}")

for host in network.hosts:
    print(
        f"Хост: {host.name} ({host.ip_address}), "
        f"Критичность: {host.criticality.value}"
    )

    for svc in host.services:
        print(f"  - Сервис: {svc.name} на порту {svc.port}")
