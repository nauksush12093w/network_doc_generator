from .models import NetworkConfig, Criticality

def process_by_hosts(network: NetworkConfig) -> dict:
    """Профиль 'по хостам': все хосты + все связи."""
    result = {"hosts": [], "connections": []}

    for host in network.hosts:
        result["hosts"].append({
            "name": host.name,
            "ip": host.ip_address,
            "os": host.os,
            "criticality": host.criticality.value,
            "services_count": len(host.services)
        })

    for conn in network.connections:
        result["connections"].append({
            "from": conn.source,
            "to": conn.target,
            "type": conn.connection_type
        })
    return result


def process_by_services(network: NetworkConfig) -> dict:
    """Профиль 'по сервисам': группировка сервисов по хостам."""
    result = {"hosts": []}

    for host in network.hosts:
        host_data = {"name": host.name, "ip": host.ip_address, "services": []}
        for svc in host.services:
            host_data["services"].append({
                "name": svc.name,
                "port": svc.port,
                "protocol": svc.protocol,
                "criticality": svc.criticality.value
            })
        result["hosts"].append(host_data)
    return result


def process_by_criticality(network: NetworkConfig) -> dict:
    """Профиль 'по критичности': только HIGH и CRITICAL."""
    important = [Criticality.HIGH, Criticality.CRITICAL]
    result = {"hosts": [], "connections": []}

    for host in network.hosts:
        has_important_service = any(s.criticality in important for s in host.services)

        if host.criticality in important or has_important_service:
            result["hosts"].append({
                "id": host.node_id,            # <--- ДОБАВИЛИ ID
                "name": host.name,             # <--- Красивое имя
                "type": host.node_type,        # <--- ДОБАВИЛИ ТИП
                "ip": host.ip_address,
                "criticality": host.criticality.value,
                "services": [
                    {"name": s.name, "criticality": s.criticality.value}
                    for s in host.services
                    if s.criticality in important
                ]
            })

    # Связи остаются по ID
    important_names = {h["id"] for h in result["hosts"]}
    for conn in network.connections:
        if conn.source in important_names and conn.target in important_names:
            result["connections"].append({
                "from": conn.source,
                "to": conn.target,
                "type": conn.connection_type
            })
    return result

    important_names = {h["name"] for h in result["hosts"]}
    for conn in network.connections:
        if conn.source in important_names and conn.target in important_names:
            result["connections"].append({
                "from": conn.source,
                "to": conn.target,
                "type": conn.connection_type
            })
    return result