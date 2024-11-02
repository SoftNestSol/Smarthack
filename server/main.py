import csv
import heapq
import os
import requests

from models import Connection, Customer, Demand, Movement, Refinery, Tank

API_KEY = "7bcd6334-bc2e-4cbf-b9d4-61cb9e868869"
API_URL = "http://localhost:8080/api/v1"

demands_queue = []


def read_csv_file(file_name):
    with open(os.path.join("data", file_name), newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        data = [dict(row) for row in reader]
    return data


def end_session():
    url = API_URL + "/session/end"
    requests.post(url, headers={"API-KEY": API_KEY})


def get_movements(response):
    if "demand" not in response:
        return []

    demands = [Demand(**demand) for demand in response["demand"]]
    for demand in demands:
        heapq.heappush(demands_queue, demand)

    movements = []
    for demand in demands_queue:
        for connection in connections:
            if connection.to_id == demand.customer_id:
                movement = {"connectionId": connection.id, "amount": demand.amount}
                movements.append(movement)
                break
        heapq.heappop(demands_queue)

    print(response["totalKpis"])
    return movements


if __name__ == "__main__":
    heapq.heapify(demands_queue)

    connections = read_csv_file("connections.csv")
    customers = read_csv_file("customers.csv")
    refineries = read_csv_file("refineries.csv")
    tanks = read_csv_file("tanks.csv")

    connections = [Connection(**connection) for connection in connections]
    customers = [Customer(**customer) for customer in customers]
    refineries = [Refinery(**refinery) for refinery in refineries]
    tanks = [Tank(**tank) for tank in tanks]

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
