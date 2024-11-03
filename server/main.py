import csv
import heapq
import os
import requests

from models import Connection, Customer, Demand, Refinery, Tank
from graph import get_shortest_path_for_customer

API_KEY = "7bcd6334-bc2e-4cbf-b9d4-61cb9e868869"
API_URL = "http://localhost:8080/api/v1"


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


def fill_tanks(tanks, demanded_tanks):
    demanded_tanks = sorted(demanded_tanks, key=lambda x: x[0], reverse=True)
    for count, tank in demanded_tanks:
        tank_id = None
        tank_cost = 0x3F3F3F3F
        for refinery in refineries:
            shortest_path = shortest_paths_for_refineries[refinery.id]
            for path in shortest_path:
                if path[0] == tank.id and path[1] < tank_cost:
                    tank_id = refinery.id
                    tank_cost = path[1]
                    break
        if tank_id is None:
            continue
        for connection in connections:
            if connection.from_id == tank_id and connection.to_id == tank.id:
                break
        if connection is None:
            continue

    return movements


def get_movements(response):
    if "demand" not in response:
        return []

    demands = [Demand(**demand) for demand in response["demand"]]
    for demand in demands:
        connection = None
        customer = None
        closest_tank = None

        for customer in customers:
            if customer.id == demand.customer_id:
                break

        if customer is None:
            continue

        shortest_path = shortest_paths_for_customers[customer.id]

        for closest_tank in tanks:
            if closest_tank.id == shortest_path[0][0]:
                break

        if closest_tank is None:
            continue

        for connection in connections:
            if connection.from_id == closest_tank.id and connection.to_id == demand.customer_id:
                break

        if connection is None:
            continue

        demand.cost = connection.get_movement_cost(demand.amount)
        demand.co2 = connection.get_movement_co2(demand.amount)
        heapq.heappush(demands_queue, demand)

    movements = []
    while demands_queue:
        demand = heapq.heappop(demands_queue)
        connection = None
        customer = None
        closest_tanks = []

        for customer in customers:
            if customer.id == demand.customer_id:
                break

        if customer is None:
            continue

        shortest_path = shortest_paths_for_customers[customer.id]

        for tank in tanks:
            if tank.id in [path[0] for path in shortest_path[:2]]:
                closest_tanks.append(tank)
                if len(closest_tanks) == 2:
                    break

        for count, tank in demanded_tanks:
            if tank.id == closest_tanks[0].id or (
                len(closest_tanks) == 2 and tank.id == closest_tanks[1].id
            ):
                demanded_tanks.remove((count, tank))
                demanded_tanks.append((count + 1, tank))
                break

        if len(closest_tanks) == 0:
            continue

        if closest_tanks[0].initial_stock >= demand.amount:
            for connection in connections:
                if (
                    connection.from_id == closest_tanks[0].id
                    and connection.to_id == demand.customer_id
                ):
                    break

            if connection is None:
                continue

            closest_tanks[0].initial_stock -= demand.amount
            movement = {"connectionId": connection.id, "amount": demand.amount}
            movements.append(movement)

        else:
            connection_one = None
            for connection_one in connections:
                if (
                    connection_one.from_id == closest_tanks[0].id
                    and connection_one.to_id == demand.customer_id
                ):
                    break

            if connection_one is None or len(closest_tanks) == 1:
                continue

            connection_two = None
            for connection_two in connections:
                if (
                    connection_two.from_id == closest_tanks[1].id
                    and connection_two.to_id == connection_one.from_id
                ):
                    break

            if connection_two is None:
                continue

            closest_tanks[1].initial_stock -= demand.amount - closest_tanks[0].initial_stock
            closest_tanks[0].initial_stock += demand.amount - closest_tanks[0].initial_stock
            closest_tanks[0].initial_stock -= demand.amount
            movement = {"connectionId": connection_two.id, "amount": demand.amount}
            movements.append(movement)
            movement = {"connectionId": connection_one.id, "amount": demand.amount}
            movements.append(movement)

    # movements += fill_tanks(tanks, demanded_tanks)
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
