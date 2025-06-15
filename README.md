# Podcast Briefing App

This Streamlit application generates weekly lecture briefings using content from Google Drive. It summarizes materials with OpenAI GPT and converts text to audio using Google Cloud Text-to-Speech so students can listen to concise podcasts for each class.

## Prerequisites

- **Python** 3.11+
- **Streamlit**
- Google Cloud service account credentials (Drive API & Text-to-Speech)
- An **OpenAI API key**

## Installation

1. Clone this repository and change into the directory.
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.streamlit/secrets.toml` file and add your Google credentials and semester start date. The service account JSON must be stored as a multi-line string:

```toml
gcp_tts_key = """
{ "type": "service_account", ... }
"""
semester_start = "2024-03-04"  # example date
```

Export your OpenAI API key before running the app:

```bash
export OPENAI_API_KEY="your-openai-key"
```

## Running the App

Launch the Streamlit application with:

```bash
streamlit run app.py
```

By default the interface will be available at `http://localhost:8501`.
