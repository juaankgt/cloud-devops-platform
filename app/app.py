import os
import time

import psycopg
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_db_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "tasks"),
        user=os.getenv("POSTGRES_USER", "devops"),
        password=os.getenv("POSTGRES_PASSWORD", "devops_password"),
    )


def initialize_database():
    for attempt in range(10):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS tasks (
                            id SERIAL PRIMARY KEY,
                            title VARCHAR(255) NOT NULL,
                            completed BOOLEAN NOT NULL DEFAULT FALSE
                        );
                        """
                    )
                conn.commit()

            print("Database initialized successfully.")
            return

        except psycopg.OperationalError as exc:
            print(f"Database not ready. Attempt {attempt + 1}/10")
            print(exc)
            time.sleep(2)

    raise RuntimeError("Could not connect to PostgreSQL.")


@app.route("/")
def home():
    return jsonify(
        {
            "application": "cloud-devops-platform",
            "status": "running",
        }
    )


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/db-health")
def db_health():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()

        return jsonify({"database": "healthy"})

    except Exception as exc:
        return jsonify(
            {
                "database": "unhealthy",
                "error": str(exc),
            }
        ), 503


@app.route("/tasks", methods=["GET"])
def get_tasks():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, completed
                FROM tasks
                ORDER BY id;
                """
            )

            tasks = [
                {
                    "id": row[0],
                    "title": row[1],
                    "completed": row[2],
                }
                for row in cur.fetchall()
            ]

    return jsonify(tasks)


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "title is required"}), 400

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tasks (title)
                VALUES (%s)
                RETURNING id, title, completed;
                """,
                (data["title"],),
            )

            row = cur.fetchone()

        conn.commit()

    return jsonify(
        {
            "id": row[0],
            "title": row[1],
            "completed": row[2],
        }
    ), 201


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000)
