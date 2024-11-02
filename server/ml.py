from flask import Flask, Response, request
import requests

API_KEY = "7bcd6334-bc2e-4cbf-b9d4-61cb9e868869"
app = Flask(__name__)


@app.route("/start", methods=["POST"])
def start():
    try:
        url = "http://localhost:8080/api/v1/session/start"
        headers = {"API-KEY": API_KEY}
        response = requests.post(url, headers=headers)

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "application/json"),
        )

    except requests.exceptions.RequestException as exception:
        return Response(str(exception), status=500)


@app.route("/end", methods=["POST"])
def end():
    try:
        url = "http://localhost:8080/api/v1/session/end"
        headers = {"API-KEY": API_KEY}
        response = requests.post(url, headers=headers)

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "application/json"),
        )

    except requests.exceptions.RequestException as exception:
        return Response(str(exception), status=500)


@app.route("/play", methods=["POST"])
def play():
    try:
        session_id = request.headers.get("SESSION-ID")
        url = "http://localhost:8080/api/v1/play/round"
        headers = {"API-KEY": API_KEY, "SESSION-ID": session_id, "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=request.json)

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "application/json"),
        )

    except requests.exceptions.RequestException as exception:
        return Response(str(exception), status=500)


if __name__ == "__main__":
    app.run(debug=True)
