import os
import argparse
import requests
import pydig
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("XC_API_TOKEN")
API_URL = os.getenv("XC_API_URL")

def get_namespaces(api_token, api_url_base):

    headers = {
        "Authorization": f"APIToken {api_token}",
        "Content-Type": "application/json"
    }
    ns_list_url = f"{api_url_base}/web/namespaces"

    response = requests.get(ns_list_url, headers=headers)
    response.raise_for_status()
    data = response.json()

    # Extract and return namespace names
    return [item['name'] for item in data.get('items', [])]


def print_acme_cnames(api_token, namespace, api_url_base, args):
    # Text Colour
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BLUE = '\033[94m'
    
    headers = {
        "Authorization": f"APIToken {api_token}",
        "Content-Type": "application/json"
    }

    lb_list_url = f"{api_url_base}/config/namespaces/{namespace}/http_loadbalancers"
    try:
        lb_list_resp = requests.get(lb_list_url, headers=headers)
        lb_list_resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[red]Failed to fetch LB list: {e}")
        return []

    lb_items = lb_list_resp.json().get("items", [])
    cname_records = []

    print('')
    print(f"\nACME CNAME Record Validation - Namespace: {namespace}")
    print("=" * 80)
    print("{:<40} {:<60} {:<60} {:<60} {:<10}".format("Load Balancer", "Record Name", "Expected Target", "Resolved Target", "Status"))
    print("-" * 240)

    for lb in lb_items:
        lb_name = lb.get("name")
        if not lb_name:
            continue

        lb_config_url = f"{api_url_base}/config/namespaces/{namespace}/http_loadbalancers/{lb_name}"
        try:
            lb_config_resp = requests.get(lb_config_url, headers=headers)
            lb_config_resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[red]Failed to fetch config for LB '{lb_name}': {e}")
            continue

        lb_config = lb_config_resp.json()
        dns_records = lb_config.get("spec", {}).get("auto_cert_info", {}).get("dns_records", [])

        for record in dns_records:
            if record.get("type") == "CNAME":
                name = record.get("name")
                expected = record.get("value")
                try:
                    result = pydig.query(name, 'CNAME')
                    resolved_raw = result[0] if result else None
                    resolved = resolved_raw.rstrip(".") if resolved_raw else None
                except Exception:
                    resolved = None

                if not resolved:
                    status = "Not Found"
                    status_colour = BLUE
                    resolved = ""
                    print(status_colour, "{:<40} {:<60} {:<60} {:<60} {:<10}".format(lb_name, name, expected, resolved, status), RESET)
                elif resolved == expected:
                    status = "Match"
                    status_colour = GREEN
                    if not args.failed:
                        print(status_colour, "{:<40} {:<60} {:<60} {:<60} {:<10}".format(lb_name, name, expected, resolved, status), RESET)        
                else:
                    status = "Mismatch"
                    status_colour = RED
                    print(status_colour, "{:<40} {:<60} {:<60} {:<60} {:<10}".format(lb_name, name, expected, resolved, status), RESET)

    return cname_records

def table_acme_cnames(api_token, namespace, api_url_base, args):
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from rich.live import Live

    headers = {
        "Authorization": f"APIToken {api_token}",
        "Content-Type": "application/json"
    }

    lb_list_url = f"{api_url_base}/config/namespaces/{namespace}/http_loadbalancers"
    try:
        lb_list_resp = requests.get(lb_list_url, headers=headers)
        lb_list_resp.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]Failed to fetch LB list: {e}")
        return []

    lb_items = lb_list_resp.json().get("items", [])
    cname_records = []

    print('')
    console = Console()

    table = Table(
        title=f"ACME CNAME Record Validation - Namespace: {namespace}",
        box=box.SQUARE,
        title_style="bold underline",
        show_lines=True
    )
    table.add_column("Load Balancer", style="cyan", no_wrap=True)
    table.add_column("Record Name", style="white")
    table.add_column("Expected Target", style="white")
    table.add_column("Resolved Target", style="white")
    table.add_column("Status", style="bold")

    with Live(table, console=console, refresh_per_second=4, vertical_overflow='visible'):
        for lb in lb_items:
            lb_name = lb.get("name")
            if not lb_name:
                continue

            lb_config_url = f"{api_url_base}/config/namespaces/{namespace}/http_loadbalancers/{lb_name}"
            try:
                lb_config_resp = requests.get(lb_config_url, headers=headers)
                lb_config_resp.raise_for_status()
            except requests.RequestException as e:
                console.print(f"[red]Failed to fetch config for LB '{lb_name}': {e}")
                continue

            lb_config = lb_config_resp.json()
            dns_records = lb_config.get("spec", {}).get("auto_cert_info", {}).get("dns_records", [])

            for record in dns_records:
                if record.get("type") == "CNAME":
                    name = record.get("name")
                    expected = record.get("value")
                    try:
                        result = pydig.query(name, 'CNAME')
                        resolved_raw = result[0] if result else None
                        resolved = resolved_raw.rstrip(".") if resolved_raw else None
                    except Exception:
                        resolved = None

                    if not resolved:
                        status = "[magenta]Not Found"
                    elif resolved == expected:
                        status = "[green]Match"
                    else:
                        status = "[red]Mismatch"

                    table.add_row(lb_name, name, expected, resolved or "—", status)
                    cname_records.append({
                        "lb_name": lb_name,
                        "record_name": name,
                        "record_value": expected
                    })

    return cname_records

def main():
    parser = argparse.ArgumentParser(description="Check F5 XC ACME CNAME records.")
    parser.add_argument(
        '-M',
        '--mode',
        choices=['print', 'table'],
        default='print',
        help='Choose output format: "table" or "print" (default).'
    )
    parser.add_argument(
        '-F',
        '--failed',
        action='store_true',
        help='Output only failed checks (only available for print output).'
    )
    args = parser.parse_args()

    namespaces = get_namespaces(API_TOKEN, API_URL)
    for NAMESPACE in namespaces:

        if args.mode == 'print':
            print_acme_cnames(API_TOKEN, NAMESPACE, API_URL, args)
        else:
            table_acme_cnames(API_TOKEN, NAMESPACE, API_URL, args)

if __name__ == "__main__":
    main()
