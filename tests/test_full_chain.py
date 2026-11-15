from app.components.processing.converter import convert_dict_to_network
from app.components.processing.processor import process_by_criticality
import json

raw_data = {
    "nodes": [
        {"id": "router", "name": "Маршрутизатор", "type": "network", "criticality": "high"},
        {"id": "server", "name": "Сервер", "type": "server", "criticality": "high"},
        {"id": "database", "name": "База данных", "type": "database", "criticality": "high"},
        {"id": "pc", "name": "Компьютер сотрудника", "type": "host", "criticality": "low"},
        {"id": "printer", "name": "Принтер", "type": "device", "criticality": "medium"}
    ],
    "connections": [
        ["router", "server"],
        ["server", "database"],
        ["router", "pc"],
        ["router", "printer"]
    ]
}

network = convert_dict_to_network(raw_data)

print("=== СХЕМА ПО КРИТИЧНОСТИ ===")
result = process_by_criticality(network)
print(json.dumps(result, indent=2, ensure_ascii=False))
