from flask import Flask, request, render_template_string
from flask_caching import Cache
import requests
import logging
import json

app = Flask(__name__)

long_timeout = 60 * 60 * 24 * 365 * 10  # 10 years in seconds

# Configure cache
# cache = Cache(app, config={'CACHE_TYPE': 'simple'})
cache = Cache(app, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': './cache',  # Path to the cache directory
    'CACHE_DEFAULT_TIMEOUT': None  # Optional: default cache timeout in seconds
})

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

# HTML template for the form and the result
HTML_TEMPLATE = '''
<!doctype html>
<html>
<head>
    <title>Imported Microchip Checker</title>
    <style>
        body { 
            font-family: 'Arial', sans-serif; 
            text-align: center; 
            padding: 20px; 
            background-color: #f4f4f4; 
            color: #333; 
        }
        h2 { 
            color: #009688; 
            font-size: 24px; 
            margin-bottom: 20px;
        }
        form { 
            margin: 0 auto; 
            display: inline-block; 
        }
        input[type="text"], input[type="submit"], button { 
            padding: 10px 15px; 
            margin: 5px; 
            border-radius: 20px; /* Rounded corners */
            border: 1px solid #ddd; 
            font-size: 16px;
        }
        input[type="text"] { 
            width: 250px; 
        }
        input[type="submit"], button { 
            background-color: #009688; /* Serene blue-green */
            color: white; 
            border: none; 
            cursor: pointer;
        }
        button { 
            background-color: #f44336; /* Red color for the clear button */
        }

        .loading {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.8);
            z-index: 10;
        }

        .loading p {
            font-size: 18px;
            color: #555;
        }
        .spinner { 
            border: 4px solid #f3f3f3; 
            border-top: 4px solid #009688; /* Spinner color */
            border-radius: 50%; 
            width: 50px; 
            height: 50px; 
            margin-bottom: 10px;
            animation: spin 2s linear infinite; 
        }
        @keyframes spin { 
            0% { transform: rotate(0deg); } 
            100% { transform: rotate(360deg); } 
        }
    </style>
</head>
<body>
    <h2>Enter MicroChip Number</h2>
    <form method="POST" id="chipForm">
        <input type="text" name="chip_number" pattern="\\d{15}" required title="15 digit number required">
        <input type="submit" value="Submit">
        <button type="button" onclick="clearInput()">Clear</button>
    </form>
    <div class="loading">
        <div class="spinner"></div>
        <p>Please wait for 1-2 minutes...</p>
    </div>
    {% if homepage_url %}
        <p style="font-size: 18px;">Microchip registered at : <a href="{{ homepage_url }}" style="color: #009688;">{{ homepage_url }}</a></p>
    {% elif homepage_url == '' %}
        <p style="font-size: 18px;">No microchip found.</p>
    {% endif %}
    <script>
    // When the window finishes loading, it will run this function to hide the loading element
    window.onload = function() {
        // Ensure the loading overlay is hidden when the page loads
        document.querySelector('.loading').style.display = 'none';
    };

    // This function clears the input field when the clear button is clicked
    function clearInput() {
        document.querySelector('input[type="text"]').value = '';
    }

    // Adding an event listener for the form submission
    document.getElementById('chipForm').addEventListener('submit', function() {
        // Show the loading overlay when the form is submitted
        document.querySelector('.loading').style.display = 'flex';
    });
    </script>
</body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def check_chip():
    homepage_url = None
    if request.method == 'POST':
        chip_number = request.form['chip_number']

        # Log the chip submission
        logging.info(f"Chip checked: {chip_number}")
        # Genetique Cat Checking Microchip https://genetiquebengals.com/
        if chip_number.startswith('702'):
            homepage_url = "https://pals.avs.gov.sg/"
            return render_template_string(HTML_TEMPLATE, homepage_url=homepage_url)
            
        # Check if result is in cache
        cached_url = cache.get(chip_number)
        if cached_url is not None:
            return render_template_string(HTML_TEMPLATE, homepage_url=cached_url)

        # Construct the URL with the chip number
        url = f"https://identibase-api-live.azurewebsites.net/api/chips/checkchip/{chip_number}"

        # Sending the POST request to the API
        response = requests.get(url)

        # Checking if the response is successful
        if response.status_code == 200:
            data = response.json()
            for entry in data:
                if entry.get('chipIsRegistered'):
                    homepage_url = entry.get('homepageUrl')
                    break
            if homepage_url is None:
                homepage_url = ''
        else:
            homepage_url = 'Error: Could not retrieve data'

        cache.set(chip_number, homepage_url, timeout=long_timeout)

    return render_template_string(HTML_TEMPLATE, homepage_url=homepage_url)


if __name__ == '__main__':
    app.run(debug=True)
