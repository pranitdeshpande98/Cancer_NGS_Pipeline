from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras
from flask_cors import CORS

app = Flask(__name__)

DB_CONFIG = dict(
    host="127.0.0.1",
    port=5433,
    dbname="ngs_pipeline",
    user="postgres",
    password="devpassword",
)


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/runs", methods=["POST"])
def create_run():
    data = request.get_json()
    sample_name = data["sample_name"]
    status = data.get("status", "running")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO runs (sample_name, status) VALUES (%s, %s) RETURNING id",
        (sample_name, status),
    )
    run_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"id": run_id, "sample_name": sample_name, "status": status}), 201


@app.route("/runs", methods=["GET"])
def list_runs():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM runs ORDER BY started_at DESC")
    runs = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(runs)


@app.route("/runs/<int:run_id>/variants", methods=["POST"])
def add_variants(run_id):
    variants = request.get_json()  # expects a JSON list of variant objects

    conn = get_db_connection()
    cur = conn.cursor()
    for v in variants:
        cur.execute(
            """INSERT INTO variants (run_id, chrom, position, ref, alt, consequence, clinical_significance)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (run_id, v["chrom"], v["position"], v["ref"], v["alt"],
             v.get("consequence"), v.get("clinical_significance")),
        )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"inserted": len(variants)}), 201


@app.route("/runs/<int:run_id>/variants", methods=["GET"])
def list_variants(run_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM variants WHERE run_id = %s", (run_id,))
    variants = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(variants)

@app.route("/stats")
def get_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM runs")
    total_runs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM variants")
    total_variants = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM variants WHERE clinical_significance = 'pathogenic'")
    pathogenic = cur.fetchone()[0]
    cur.close()
    conn.close()
    return jsonify({
        "total_runs": total_runs,
        "total_variants": total_variants,
        "pathogenic_variants": pathogenic,
    })


if __name__ == "__main__":
    CORS(app)
    app.run(debug=True, port=8000)