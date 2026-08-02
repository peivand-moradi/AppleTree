# AppleTree

AppleTree is a responsive Flask web prototype that helps users compare what to do with an unwanted purchase. It considers options such as returning the item to the retailer, donating it, recycling it, or disposing of it responsibly. Product details, photos, sample retailer policies, nearby-place results, and Gemini are combined to present two useful perspectives: maximizing the potential refund and reducing travel distance and environmental impact.

## Project history

AppleTree began as a first-year hackathon project completed in less than a week. Our team wanted to make product returns less confusing while encouraging people to consider both the money they could recover and the environmental cost of a return. We sketched the experience on paper, learned Figma to create the interface prototype, and built a working Flask application using Python, Gemini, and Google Places.

After the hackathon, I revisited the project and improved its security, reliability, API integration, error handling, results experience, and responsive design. The current repository represents that improved web prototype while preserving the original product concept and technical foundation.

The current project remains a proof of concept. Its retailer policies are sample data and its recommendations must be verified with the retailer or location involved.

## Original hackathon work

The original prototype established the core parts of AppleTree:

- The return-advisory concept and user flow
- Two recommendation priorities: potential refund value and shorter travel distance
- A product form collecting purchase details, location, return reason, and photos
- A Python and Flask backend
- Gemini-assisted return recommendations
- Google Places integration for nearby return-related locations
- Paper sketches and a Figma prototype created by a team learning the tool for the first time
- A tree-growth rewards concept designed to encourage sustainable choices

The proposed rewards experience allowed an apple tree to grow when a user selected the more sustainable option. After five growth stages, the concept awarded a $10 reward. This was part of the original product vision and design, but it is not implemented as a real rewards system in the current web application.

## Features

- Collects purchase details, a return reason, and product photos
- Uses Google Places to find nearby donation, recycling, and disposal locations
- Uses Gemini to compare available options, potential refund value, distance, and sustainability trade-offs
- Displays the generated comparison directly in the interface
- Validates required fields, purchase dates, image formats, and total upload size
- Handles API and configuration errors without exposing credentials
- Works across desktop and mobile layouts

## Tech stack

- Python and Flask
- HTML, CSS, and vanilla JavaScript
- Google Gemini API
- Google Places API

## Local setup

1. Clone the repository and move into it.
2. Create and activate a virtual environment.
3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and add your own API keys:

   ```env
   GEMINI_API_KEY=your_gemini_api_key
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   ```

5. Start the app:

   ```bash
   python hackathon/app.py
   ```

6. Open `http://127.0.0.1:5000` in your browser.

Never commit `.env` or real API keys. Restrict production keys to the APIs and environments that need them.

## Project structure

```text
AppleTree/
├── hackathon/
│   ├── app.py
│   ├── static/index.css
│   └── templates/index.html
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Limitations

- Retailer policies are prototype data, not live policy integrations.
- Nearby results depend on Google Places data and the location entered.
- Distance is used as a practical sustainability signal, not as a complete environmental-impact calculation.
- AI output may be incomplete or inaccurate and should be treated as advisory.
- The app does not complete a return, issue a refund, or track user rewards.
- It is currently designed as a single-user local demo rather than a deployed service.

## Future directions

- Connect to live retailer and e-commerce return policies
- Add a user-controlled comparison between refund-first and distance-first recommendations
- Implement the interactive tree-growth system from the original Figma concept
- Explore meaningful rewards without implying a partnership that does not exist
- Improve the sustainability estimate beyond distance alone
