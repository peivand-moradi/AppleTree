import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path

import requests
from google import genai
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
RETURN_POLICIES = {
    "Nike": {"return_time_limit": 60, "condition_required": "new or gently worn"},
    "Adidas": {"return_time_limit": 30, "condition_required": "unworn with tags"},
    "Amazon": {"return_time_limit": 30, "condition_required": "varies by product"},
}


def require_environment_variable(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not configured. See .env.example for setup instructions.")
    return value


def get_nearby_places(address, keyword):
    response = requests.get(
        "https://maps.googleapis.com/maps/api/place/textsearch/json",
        params={
            "query": f"{keyword} near {address}",
            "key": require_environment_variable("GOOGLE_MAPS_API_KEY"),
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") not in {"OK", "ZERO_RESULTS"}:
        raise RuntimeError(data.get("error_message", "Google Places search failed."))

    return [
        {
            "name": place.get("name", "Unknown location"),
            "address": place.get("formatted_address", "Address unavailable"),
            "rating": place.get("rating"),
        }
        for place in data.get("results", [])[:5]
    ]


def validate_form(form, photos):
    required_fields = {
        "address": "Address",
        "purchase_location": "Purchase location",
        "purchase_date": "Purchase date",
        "product_code": "Product code",
        "order_number": "Order number",
        "return_reason": "Return reason",
    }

    missing = [label for key, label in required_fields.items() if not form.get(key, "").strip()]
    if missing:
        return f"Please complete: {', '.join(missing)}."

    if form["purchase_location"] not in RETURN_POLICIES:
        return "Please choose a supported purchase location."

    try:
        purchase_date = datetime.strptime(form["purchase_date"], "%Y-%m-%d").date()
        if purchase_date > date.today():
            return "Purchase date cannot be in the future."
    except ValueError:
        return "Please enter a valid purchase date."

    valid_photos = [photo for photo in photos if photo and photo.filename]
    if not valid_photos:
        return "Please upload at least one product photo."

    for photo in valid_photos:
        if Path(secure_filename(photo.filename)).suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            return "Photos must be JPG, PNG, or WebP files."

    return None


def build_prompt(form, nearby_locations):
    policy = RETURN_POLICIES[form["purchase_location"]]
    return f"""
You are helping a customer compare realistic product return options. Treat the supplied return
policy as prototype data, not verified live policy. Do not invent prices, eligibility, or locations.

Customer details:
- Purchase location: {form['purchase_location']}
- Purchase date: {form['purchase_date']}
- Product code: {form['product_code']}
- Return reason: {form['return_reason']}
- Prototype policy: {json.dumps(policy)}
- Current date: {date.today().isoformat()}
- Nearby locations: {json.dumps(nearby_locations, indent=2)}

Use the attached product photos as supporting context. If their condition is unclear, say so.
Compare return-to-retailer, donation, recycling, and landfill only when relevant. Never claim that
an option is approved without explaining that the retailer must confirm it. Do not claim to have
searched resale sites or quote an estimated resale value.

Return concise Markdown with these headings:
## Return overview
## Options
## Recommended next step

For each option, state eligibility, location when available, potential refund ("confirm with
retailer" when unknown), and sustainability considerations. End with a one-sentence disclaimer
that this prototype is advisory and policies should be verified with the retailer.
""".strip()


def generate_analysis(form, photos):
    nearby_locations = {
        "recycling": get_nearby_places(form["address"], "recycling center"),
        "donation": get_nearby_places(form["address"], "donation center"),
        "landfill": get_nearby_places(form["address"], "landfill"),
    }

    client = genai.Client(api_key=require_environment_variable("GEMINI_API_KEY"))

    uploaded_images = []
    with tempfile.TemporaryDirectory(prefix="appletree-") as temp_directory:
        for photo in photos:
            if not photo or not photo.filename:
                continue
            filename = secure_filename(photo.filename)
            path = Path(temp_directory) / filename
            photo.save(path)
            uploaded_images.append(client.files.upload(file=path))

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            contents=[build_prompt(form, nearby_locations), *uploaded_images],
        )

        for uploaded_image in uploaded_images:
            try:
                client.files.delete(name=uploaded_image.name)
            except Exception:
                app.logger.warning("Could not delete temporary Gemini file %s", uploaded_image.name)

    if not getattr(response, "text", None):
        raise RuntimeError("Gemini returned an empty response.")
    return response.text.strip()


@app.get("/")
def index():
    return render_template("index.html", today=date.today().isoformat())


@app.post("/analyze")
def analyze_return():
    photos = request.files.getlist("photos")
    validation_error = validate_form(request.form, photos)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    try:
        result = generate_analysis(request.form, photos)
        return jsonify({"result": result})
    except (requests.RequestException, RuntimeError) as error:
        app.logger.warning("Analysis could not be completed: %s", error)
        return jsonify({"error": str(error)}), 502
    except Exception:
        app.logger.exception("Unexpected analysis failure")
        return jsonify({"error": "The analysis could not be completed. Please try again."}), 500


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "The uploaded files are too large. The total limit is 12 MB."}), 413


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
