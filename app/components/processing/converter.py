from .models import Host, Service, NetworkConfig, Criticality, Connection

def convert_dict_to_network(data: dict) -> NetworkConfig:
    network = NetworkConfig()

    for node in data.get("nodes", []):

        crit_str = node.get("criticality", "low").capitalize()
        crit_enum = Criticality(crit_str)

        services = []

        for service_data in node.get("services", []):

            service_crit_str = service_data.get(
                "criticality", "low"
            ).capitalize()

            service_crit_enum = Criticality(service_crit_str)

            service = Service(
                name=service_data["name"],
                port=int(service_data["port"]),
                protocol=service_data.get("protocol", "TCP"),
                criticality=service_crit_enum
            )

            services.append(service)

        host = Host(
            name=node.get("name", node["id"]),
            ip_address=node.get("ip_address", "0.0.0.0"),
            os=node.get("os", "Unknown"),
            criticality=crit_enum,
            services=services,
            node_id=node["id"],
            node_type=node.get("type", "host")
        )

        network.hosts.append(host)

    for conn_data in data.get("connections", []):

        source_id, target_id = conn_data

        connection = Connection(
            source=source_id,
            target=target_id,
            connection_type="Network"
        )

        network.connections.append(connection)

    return network
