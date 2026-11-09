from dataclasses import dataclass, field
from typing import List
from enum import Enum

class Criticality(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

@dataclass
class Service:
    """Описывает сервис (например, веб-сервер, база данных)"""
    name: str
    port: int
    protocol: str = "TCP"
    criticality: Criticality = Criticality.LOW

@dataclass
class Host:
    """Описывает хост (сервер, компьютер, сетевое устройство)"""
    name: str               # Красивое имя (Маршрутизатор)
    ip_address: str         # IP (или заглушка)
    os: str = "Unknown"
    criticality: Criticality = Criticality.LOW
    services: List[Service] = field(default_factory=list)
    
    # НОВЫЕ ПОЛЯ:
    node_id: str = ""       # Короткий ID (router, server)
    node_type: str = "host" # Тип (network, server, database, device, host)

@dataclass
class Connection:
    """Описывает связь между двумя хостами или сервисами"""
    source: str
    target: str
    connection_type: str = "Network"

@dataclass
class NetworkConfig:
    """Главный контейнер, который хранит всю информацию о сети"""
    hosts: List[Host] = field(default_factory=list)
    connections: List[Connection] = field(default_factory=list)

