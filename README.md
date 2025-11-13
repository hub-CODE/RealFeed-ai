# RealFeed-ai: News Authenticity Checker

RealFeed-ai helps you figure out whether a news headline or short article is real or fake using machine learning.  
Built with Flask and Hugging Face Transformers, it’s designed to make news verification simple for everyone.

---

## Features

- Detects if a news headline or short article is likely real or fake.  
- Runs an AI model fine-tuned for fake news detection.  
- Lets users input custom headlines or articles for quick checking.  
- Fetches trending global headlines in real time using NewsAPI.  
- Lightweight, fast, and easy to extend for additional AI tools.

---

## How It Works

1. Enter a news headline or short article into the text box.  
2. The model analyzes it and predicts whether it’s real or fake.  
3. The homepage also displays live headlines pulled from NewsAPI.

---

## Tech Stack

- **Backend:** Python (Flask)  
- **AI Model:** Hugging Face Transformers (Fine-tuned BERT)  
- **APIs:** NewsAPI for live headlines  
- **Frontend:** HTML, CSS, JavaScript  

---

## Installation

Follow these steps to set up RealFeed locally:

```
# Clone the repository
git clone https://github.com/yourusername/RealFeed.git

# Navigate into the project folder
cd RealFeed

# Install dependencies
pip install -r requirements.txt

# Add your NewsAPI key to a .env file
# Example:
# NEWS_API_KEY=your_api_key_here

# Run the Flask app
flask run
```

After running, open your browser and go to `http://127.0.0.1:5000` to start using RealFeed.

---

## Why Use RealFeed

With so much information shared online, it’s not always clear what’s true.  
RealFeed helps you cross-check facts instantly using reliable machine learning predictions trained on news datasets.

---

## Future Plans

- Add detection for deepfake images and videos.  
- Build explainable AI features to show how predictions are made.  
- Improve model accuracy with newer news datasets.

---

## Contributing

Contributions are welcome.  
If you have ideas for new features or notice something that can be improved, feel free to open an issue or a pull request.

---

## License

This project is open-source under the MIT License.  
See the `LICENSE` file for details.

