from app.components.processing.sample_data import create_sample_network
from app.components.processing.processor import process_by_hosts, process_by_services, process_by_criticality
import json

# Загружаем тестовые данные
network = create_sample_network()

print("=== ПРОФИЛЬ 'ПО ХОСТАМ' ===")
print(json.dumps(process_by_hosts(network), indent=2, ensure_ascii=False))

print("\n=== ПРОФИЛЬ 'ПО СЕРВИСАМ' ===")
print(json.dumps(process_by_services(network), indent=2, ensure_ascii=False))

print("\n=== ПРОФИЛЬ 'ПО КРИТИЧНОСТИ' ===")
print(json.dumps(process_by_criticality(network), indent=2, ensure_ascii=False))
