from flask import Flask, render_template, request, redirect, url_for, flash
import csv
from pathlib import Path

app = Flask(__name__)
app.secret_key = "crop-record-demo-key"

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "crops.csv"
FIELDS = ["id", "farmer_name", "crop_name", "field_name", "area", "sowing_date", "harvest_date", "season", "expected_yield"]


def ensure_file():
    DATA_FILE.parent.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        with DATA_FILE.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def read_crops():
    ensure_file()
    with DATA_FILE.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_crops(crops):
    with DATA_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(crops)


def next_id(crops):
    ids = [int(c["id"]) for c in crops if c.get("id", "").isdigit()]
    return str(max(ids, default=0) + 1)


@app.route("/")
def index():
    crops = read_crops()
    total_area = sum(float(c["area"]) for c in crops if c.get("area"))
    crop_types = len({c["crop_name"].strip().lower() for c in crops if c.get("crop_name")})
    seasons = {c["season"] for c in crops if c.get("season")}
    return render_template("index.html", crops=crops, total_area=total_area,
                           crop_types=crop_types, season_count=len(seasons))


@app.route("/add", methods=["POST"])
def add_crop():
    fields = [f for f in FIELDS if f != "id"]
    data = {field: request.form.get(field, "").strip() for field in fields}
    required = ["farmer_name", "crop_name", "field_name", "area", "sowing_date", "season"]

    if any(not data[f] for f in required):
        flash("Please fill all required fields.", "error")
        return redirect(url_for("index"))

    try:
        area = float(data["area"])
        if area <= 0:
            raise ValueError
    except ValueError:
        flash("Area must be a positive number.", "error")
        return redirect(url_for("index"))

    if data["harvest_date"] and data["harvest_date"] < data["sowing_date"]:
        flash("Harvest date cannot be before sowing date.", "error")
        return redirect(url_for("index"))

    crops = read_crops()
    data["id"] = next_id(crops)
    crops.append(data)
    write_crops(crops)
    flash("Crop record added successfully.", "success")
    return redirect(url_for("index"))


@app.route("/update/<record_id>", methods=["POST"])
def update_crop(record_id):
    crops = read_crops()
    for crop in crops:
        if crop["id"] == record_id:
            for field in FIELDS:
                if field != "id":
                    crop[field] = request.form.get(field, "").strip()
            try:
                if float(crop["area"]) <= 0:
                    raise ValueError
            except ValueError:
                flash("Area must be a positive number.", "error")
                return redirect(url_for("index"))
            if crop["harvest_date"] and crop["harvest_date"] < crop["sowing_date"]:
                flash("Harvest date cannot be before sowing date.", "error")
                return redirect(url_for("index"))
            write_crops(crops)
            flash("Crop record updated successfully.", "success")
            return redirect(url_for("index"))
    flash("Crop record not found.", "error")
    return redirect(url_for("index"))


@app.route("/delete/<record_id>", methods=["POST"])
def delete_crop(record_id):
    crops = read_crops()
    new_crops = [c for c in crops if c["id"] != record_id]
    if len(new_crops) == len(crops):
        flash("Crop record not found.", "error")
    else:
        write_crops(new_crops)
        flash("Crop record deleted.", "success")
    return redirect(url_for("index"))


@app.route("/clear", methods=["POST"])
def clear_all():
    write_crops([])
    flash("All crop records have been cleared.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    ensure_file()
    app.run(debug=True)
