from app.app import app


def test_home():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json()["status"] == "running"


def test_health():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"

def test_create_task():
    client = app.test_client()

    response = client.post(
	"/tasks",
	json={"title": "Learn Kubernetes"}
    )

    assert response.status_code == 201
    assert response.get_json()["title"] == "Learn Kubernetes"

    response = client.get("/tasks")

    tasks = response.get_json()

    assert any(task["title"] == "Learn Kubernetes" for task in tasks)


