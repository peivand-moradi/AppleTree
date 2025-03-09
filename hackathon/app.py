from flask import Flask, request, jsonify, render_template
import os
import json
from datetime import datetime
import google.generativeai as genai
from datetime import datetime

current_date = datetime.now().strftime("%Y-%m-%d")

# Configure Gemini AI
genai.configure(api_key="AIzaSyALHO1TzXQ7cesq94Gb08N_8gg70F70pdM")
model = genai.GenerativeModel("gemini-1.5-pro-latest")

# Initialize Flask app
app = Flask(__name__)

# Ensure uploads directory exists
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Mock return policies
return_policies = {
    "Nike": {"return_time_limit": 60, "condition_required": "new or gently worn"},
    "Adidas": {"return_time_limit": 30, "condition_required": "unworn with tags"},
    "Amazon": {"return_time_limit": 30, "condition_required": "varies by product"}
}

# Store user data temporarily
user_data = {}

import requests

# Function to get nearby places
def get_nearby_places(address, keyword):
    API_KEY = "AIzaSyBcrOJ7DTqXnLzlmD-75uSg1IOb006F2uU"  
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={keyword}+near+{address}&key={API_KEY}"

    response = requests.get(url)
    data = response.json()

    locations = []
    for place in data.get("results", [])[:5]:  # Get top 5 locations
        locations.append({
            "name": place["name"],
            "address": place["formatted_address"],
            "rating": place.get("rating", "N/A")
        })

    return locations

@app.route("/")
def index():
    return render_template("index.html")  # Renders the frontend

@app.route("/check_return", methods=["POST"])
def check_return():
    try:
        # Get form data
        address = request.form.get("address")
        purchase_location = request.form.get("purchase_location")
        purchase_date = request.form.get("purchase_date")
        product_code = request.form.get("product_code")
        order_number = request.form.get("order_number")
        return_reason = request.form.get("return_reason")
        uploaded_files = request.files.getlist("photos")

        # Store user data
        user_data["address"] = address
        user_data["purchase_location"] = purchase_location
        user_data["purchase_date"] = purchase_date
        user_data["product_code"] = product_code
        user_data["order_number"] = order_number
        user_data["return_reason"] = return_reason

        uploaded_file_paths = []
        if uploaded_files:
            for file in uploaded_files:
                if file.filename:
                    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
                    file.save(filepath)
                    uploaded_file_paths.append(filepath)

        user_data["photos"] = uploaded_file_paths

        # Check if images were uploaded
        if not uploaded_file_paths:
            return jsonify({"result": "No images uploaded!"}), 400

        return jsonify({"result": "Return request received! Processing..."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/result", methods=["GET"])
def analysis():
    try:
        if not user_data:
            return jsonify({"error": "No return request found. Submit the form first."}), 400
        address = user_data.get("address")

        recycling_centers = get_nearby_places(address, "recycling center")
        landfills = get_nearby_places(address, "landfill")
        donation_centers = get_nearby_places(address, "donation center")
        # Generate AI prompt
        prompt = f"""
        A customer wants to return a product. Details:

        - Address: {user_data["address"]}
        - Purchase Location: {user_data["purchase_location"]}
        - Purchase Date: {user_data["purchase_date"]}
        - Product Code: {user_data["product_code"]}
        - Order Number: {user_data["order_number"]}
        - Reason: {user_data["return_reason"]}
        - Photos: {user_data["photos"]}
         Recycling Centers: {json.dumps(recycling_centers, indent=2)}
         Landfills: {json.dumps(landfills, indent=2)}
         Donation Centers: {json.dumps(donation_centers, indent=2)}

        The current date is: **{current_date}**
        The customer has uploaded images showing the product condition.
        Here are the return policies: {json.dumps(return_policies, indent=2)}
        Analyse the returning reason, and based on this analysis and checking photos of prodyct sent by the customer and date of purchase examin the condition of product.
        - If return was approved based on company policy, the company which is mentioned in purchase location, give the option of returning to the company and determine whether should the customer drop it in a shipping place or return it directly to the store where they bought it.The amount of money returned to customer would be same as the product. Also if the product's destination waas not same as one where customer drops it, this option would not be sustainable.For example, if customer drops the package at a post office and then again post office would ship it to company, then it is not sustainable. But if customer has to go to closest nike in person that counts as sustainable becuase less energy would be consumed.
        - if a product is not in good condition, not usable at all, If it could be recycled give the closest recycling location, and if it is not recyclable give the closest location of landfield. No money would be given back to customer. The recycling option would be sustainable.
        - Give online retail options with closest value found on that platform on internet for the product with same brand and condition for refund.
        -Give a list of five closest to customer location for donation where no money would be given to customer
        list all these options with (option name, location, return money value in dollars, sustainable or not)
        Return the response in the following structured JSON format:

        Return the response as a **structured Markdown text**, following this format:

        ```
        ## Return Analysis for Product {user_data["product_code"]}

        **Customer Reason:** "{user_data["return_reason"]}"

        **Purchase Location:** {user_data["purchase_location"]}
        **Purchase Date:** {user_data["purchase_date"]}

        ### Return Options:
        1. **Return to {user_data["purchase_location"]}** - ✅ Approved/❌ Rejected (Reason)
        2. **Recycling** - ✅ Possible (Closest recycling center: XYZ)
        3. **Landfill Disposal** - ❌ Not sustainable
        4. **Resale** - ✅ Suggested (Estimated value on eBay: $XX)
        5. **Donation** - ✅ Suggested (Charity: XYZ)

        ```
        for all of them mention sustainibility, aproval.
        Ensure your response follows this format exactly.
        """
        # Get AI-generated response
        response = model.generate_content(prompt)
        try:
            result = response.candidates[0].content.parts[0].text.strip() # AI Response 
            return jsonify({"result": result})  # Return the Markdown response
        except AttributeError:
            return jsonify({"error": "Failed to extract AI response. Check response structure."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
