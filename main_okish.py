import csv
import heapq
import os
import requests

from models import Connection, Customer, Demand, Refinery, Tank
from graph import get_shortest_path_for_customer

API_KEY = "7a30dcf7-483b-4978-a4d9-eae5ac677c7a"
API_URL = "https://smarthack2024-eval.cfapps.eu12.hana.ondemand.com/api/v1"


def read_csv_file(file_name):
    with open(os.path.join("data", file_name), newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        data = [dict(row) for row in reader]
    return data


def end_session():
    url = API_URL + "/session/end"
    requests.post(url, headers={"API-KEY": API_KEY})


def get_graph_without_refineries(connections, refineries):
    graph = {}

    connections_without_refineries = [
        connection
        for connection in connections
        if connection.from_id not in [refinery.id for refinery in refineries]
    ]

    for connection in connections_without_refineries:
        if connection.to_id not in graph:
            graph[connection.to_id] = []
        graph[connection.to_id].append((connection.from_id, connection.lead_time_days))

    return graph


def get_graph_without_customers(connections, customers):
    graph = {}

    connections_without_customers = [
        connection
        for connection in connections
        if connection.to_id not in [customer.id for customer in customers]
    ]

    for connection in connections_without_customers:
        if connection.from_id not in graph:
            graph[connection.from_id] = []
        graph[connection.from_id].append((connection.to_id, connection.lead_time_days))

    return graph


def fill_tanks(tanks, demanded_tanks, connections, refineries, shortest_paths_for_refineries):
    """
    Fill tanks while respecting all model constraints, minimizing penalties,
    and ensuring refinery output is managed to prevent overflow.
    """
    movements = []
    refinery_daily_output = {refinery.id: 0 for refinery in refineries}
    connection_usage_tracker = {connection.id: 0 for connection in connections}

    # Prioritize tanks by demand intensity, risk of underfill, and days remaining for demand
    demanded_tanks = sorted(
        demanded_tanks,
        key=lambda x: (
            x[0],  # demand count
            (
                float(x[1].capacity - x[1].initial_stock) / x[1].capacity if x[1].capacity else 0
            ),  # risk factor
            -x[1].capacity,  # prefer larger tanks
            x[1].days_remaining,  # prioritize tanks with closer deadlines
        ),
        reverse=True,
    )

    for refinery in refineries:
        remaining_output = float(refinery.max_output) - refinery_daily_output[refinery.id]
        if remaining_output <= 0:
            continue  # Skip if refinery has no output left for the day

        for demand_count, tank in demanded_tanks:
            if demand_count == 0:
                continue

            space_available = tank.capacity - tank.initial_stock
            max_input_possible = min(space_available, float(tank.max_input))
            needed_amount = min(remaining_output, max_input_possible)

            # Find the best direct connection for the refinery to the tank
            best_connection = next(
                (
                    conn
                    for conn in connections
                    if conn.from_id == refinery.id and conn.to_id == tank.id
                ),
                None,
            )

            if best_connection is None:
                continue  # Skip if no direct connection is available

            # Enforce hard limit on connection capacity
            max_transferable = (
                best_connection.max_capacity - connection_usage_tracker[best_connection.id]
            )
            if max_transferable <= 0:
                continue  # Skip this movement if the connection is fully utilized

            movement_amount = min(needed_amount, max_transferable)

            if movement_amount > 0:
                movement = {"connectionId": best_connection.id, "amount": movement_amount}
                movements.append(movement)

                # Update tracking data
                tank.initial_stock += movement_amount
                refinery_daily_output[refinery.id] += movement_amount
                connection_usage_tracker[best_connection.id] += movement_amount
                remaining_output -= movement_amount

                if remaining_output <= 0:
                    break  # Stop movements from this refinery if output limit is reached

    return movements


def get_movements(response):
    if "demand" not in response:
        return []

    # Initialize demands with cost and CO2 calculations
    demands = [Demand(**demand) for demand in response["demand"]]
    demands_by_day = {}

    # Group demands by start_day for better planning
    for demand in demands:
        if demand.start_day not in demands_by_day:
            demands_by_day[demand.start_day] = []
        demands_by_day[demand.start_day].append(demand)

    movements = []
    tank_states = {tank.id: tank.initial_stock for tank in tanks}

    # Process demands by start_day
    for day in sorted(demands_by_day.keys()):
        day_demands = demands_by_day[day]

        # Sort demands by urgency (end_day - start_day) and volume
        day_demands.sort(key=lambda x: (x.end_day - x.start_day, x.amount))

        for demand in day_demands:
            customer = next((c for c in customers if c.id == demand.customer_id), None)
            if not customer:
                continue

            shortest_path = shortest_paths_for_customers[customer.id]
            possible_sources = []

            # Find potential source tanks with available stock
            for path in shortest_path[:3]:  # Consider up to 3 closest tanks
                tank = next((t for t in tanks if t.id == path[0]), None)
                if tank and tank_states[tank.id] > 0:
                    possible_sources.append((tank, tank_states[tank.id], path))

            if not possible_sources:
                continue

            # Sort sources by a combination of distance and available stock
            possible_sources.sort(key=lambda x: (-x[1], len(x[2])))

            amount_needed = demand.amount
            movements_for_demand = []

            # Try to fulfill demand using minimum number of tanks
            for source_tank, available_stock, path in possible_sources:
                if amount_needed <= 0:
                    break

                usable_amount = min(available_stock, amount_needed)
                if usable_amount <= 0:
                    continue

                # Find direct connection to customer
                connection = next(
                    (
                        c
                        for c in connections
                        if c.from_id == source_tank.id and c.to_id == demand.customer_id
                    ),
                    None,
                )

                if connection:
                    movement = {"connectionId": connection.id, "amount": usable_amount}
                    movements_for_demand.append(movement)
                    tank_states[source_tank.id] -= usable_amount
                    amount_needed -= usable_amount
                    demand.partially_fullfill(usable_amount)
                else:
                    # Handle multi-hop transfer if needed
                    transfer_path = []
                    current_id = source_tank.id

                    for next_id in path[1:]:
                        connection = next(
                            (
                                c
                                for c in connections
                                if c.from_id == current_id and c.to_id == next_id
                            ),
                            None,
                        )
                        if not connection:
                            break
                        transfer_path.append(connection)
                        current_id = next_id

                    if len(transfer_path) == len(path) - 1:
                        # Add all movements in path
                        for conn in transfer_path:
                            movement = {"connectionId": conn.id, "amount": usable_amount}
                            movements_for_demand.append(movement)
                        tank_states[source_tank.id] -= usable_amount
                        amount_needed -= usable_amount
                        demand.partially_fullfill(usable_amount)

            # Add movements in optimal order
            movements.extend(sorted(movements_for_demand, key=lambda x: x["connectionId"]))

    # print(response["penalties"])
    print(response["totalKpis"])
    return movements


if __name__ == "__main__":
    demands_queue = []
    heapq.heapify(demands_queue)

    connections = read_csv_file("connections.csv")
    customers = read_csv_file("customers.csv")
    refineries = read_csv_file("refineries.csv")
    tanks = read_csv_file("tanks.csv")

    connections = [Connection(**connection) for connection in connections]
    customers = [Customer(**customer) for customer in customers]
    refineries = [Refinery(**refinery) for refinery in refineries]
    tanks = [Tank(**tank) for tank in tanks]

    demanded_tanks = [(0, tank) for tank in tanks]

    graph_without_refineries = get_graph_without_refineries(connections, refineries)
    shortest_paths_for_customers = {
        customer.id: get_shortest_path_for_customer(graph_without_refineries, customer.id)
        for customer in customers
    }

    graph_without_customers = get_graph_without_customers(connections, customers)
    shortest_paths_for_refineries = {
        refinery.id: get_shortest_path_for_customer(graph_without_customers, refinery.id)
        for refinery in refineries
    }

    url = API_URL + "/session/start"
    session_id = requests.post(url, headers={"API-KEY": API_KEY}).content

    movements = []
    day = 0

    while True:
        if day > 42:
            end_session()
            break

        try:
            url = API_URL + "/play/round"
            headers = {
                "API-KEY": API_KEY,
                "SESSION-ID": session_id,
                "Content-Type": "application/json",
            }
            data = {
                "day": day,
                "movements": movements,
            }
            response = requests.post(url, headers=headers, json=data)
            movements = get_movements(dict(response.json()))
            day = day + 1

        except requests.exceptions.RequestException as exception:
            end_session()
            print(exception)
            break
