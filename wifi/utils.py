from librouteros import connect
from librouteros.exceptions import TrapError

def configure_router(data):
    """
    Configures a MikroTik router using RouterOS API.
    :param data: A dictionary containing router configuration details (e.g., IP, username, password).
    :return: Success or error message.
    """
    try:
        # Establish connection to the router
        api = connect(
            host=data.get("host"),
            username=data.get("username"),
            password=data.get("password"),
            port=data.get("port", 8728)  # Default MikroTik API port
        )

        # Example configuration: Adding a new firewall rule
        firewall_rule = {
            "chain": "input",
            "action": "accept",
            "src-address": data.get("src_address", "192.168.20.1/24"),
        }
        api(cmd="/ip/firewall/filter/add", **firewall_rule)

        return "Router configured successfully!"

    except TrapError as e:
        raise Exception(f"Router configuration error: {e}")

    except Exception as e:
        raise Exception(f"Failed to connect to router: {e}")
