import csv
import os
import requests

from models import Connection, Customer, Demand, Refinery, Tank

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


def solve(response):
    print(response["totalKpis"])


if __name__ == "__main__":
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

    day = 0
    response = None

    while True:
        if day > 43:
            end_session()
            break

        if day > 0:
            solve(dict(response.json()))
            break

        data = {
            "day": day,
            "movements": [],
        }

        try:
            url = API_URL + "/play/round"
            headers = {
                "API-KEY": API_KEY,
                "SESSION-ID": session_id,
                "Content-Type": "application/json",
            }
            response = requests.post(url, headers=headers, json=data)
            day = day + 1

        except requests.exceptions.RequestException as exception:
            end_session()
            print(exception)
            break
