from .models import NetworkConfig, Criticality


def process_by_hosts(network: NetworkConfig) -> dict:

    result = {
        "hosts": [],
        "connections": []
    }

    for host in network.hosts:
        result["hosts"].append({
            "id": host.node_id,
            "name": host.name,
            "ip": host.ip_address,
            "os": host.os,
            "type": host.node_type,
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

    result = {
        "hosts": []
    }

    for host in network.hosts:

        host_data = {
            "id": host.node_id,
            "name": host.name,
            "ip": host.ip_address,
            "criticality": host.criticality.value,
            "services": []
        }

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

    important = [
        Criticality.HIGH,
        Criticality.CRITICAL
    ]

    result = {
        "hosts": [],
        "connections": []
    }

    for host in network.hosts:

        has_important_service = any(
            service.criticality in important
            for service in host.services
        )

        if host.criticality in important or has_important_service:

            result["hosts"].append({
                "id": host.node_id,
                "name": host.name,
                "type": host.node_type,
                "ip": host.ip_address,
                "criticality": host.criticality.value,
                "services": [
                    {
                        "name": service.name,
                        "criticality": service.criticality.value
                    }
                    for service in host.services
                    if service.criticality in important
                ]
            })

    important_ids = {
        host["id"]
        for host in result["hosts"]
    }

    for conn in network.connections:

        if (
            conn.source in important_ids
            and conn.target in important_ids
        ):
            result["connections"].append({
                "from": conn.source,
                "to": conn.target,
                "type": conn.connection_type
            })

    return result
