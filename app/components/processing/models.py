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
    name: str
    port: int
    protocol: str = "TCP"
    criticality: Criticality = Criticality.LOW

@dataclass
class Host:
    name: str               
    ip_address: str        
    os: str = "Unknown"
    criticality: Criticality = Criticality.LOW
    services: List[Service] = field(default_factory=list)
    
    node_id: str = ""
    node_type: str = "host"

@dataclass
class Connection:
    source: str
    target: str
    connection_type: str = "Network"

@dataclass
class NetworkConfig:
    hosts: List[Host] = field(default_factory=list)
    connections: List[Connection] = field(default_factory=list)

