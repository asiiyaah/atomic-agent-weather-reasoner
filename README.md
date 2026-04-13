# 🤖 Agentic Weather Planner ⛅

A conversational AI weather assistant built with Streamlit, Groq (LLaMA 3.1), and OpenWeatherMap. Ask about weather anywhere in the world in plain English — including follow-up questions, activity planning, and typo-tolerant city search.

---

## Features

- 🌍 **Global weather coverage** — any city worldwide
- 🔍 **Typo handling** — "Landan" resolves to London automatically
- 🧠 **Conversation memory** — follow-up questions remember previous context
- 🎯 **Intent-aware** — only fetches weather when relevant, skips tool calls for casual messages
- 📍 **Geocoding-first** — uses coordinates for maximum accuracy instead of raw city name lookup

---

## Tech Stack

| Component | Tool |
|---|---|
| UI | Streamlit |
| LLM | Groq — `llama-3.1-8b-instant` |
| Weather API | OpenWeatherMap |
| Geocoding | OpenWeatherMap Geocoding API |

---

## Project Structure

```
.
├── app.py        # Main Streamlit app and agent logic
├── tools.py      # Weather fetching tool with geocoding
├── .env          # API keys (not committed)
└── README.md
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/agentic-weather-planner.git
cd agentic-weather-planner
```

### 2. Install dependencies

```bash
pip install streamlit groq requests python-dotenv
```

### 3. Create a `.env` file

```env
GROQ_API_KEY=your_groq_api_key
WEATHER_API_KEY=your_openweathermap_api_key
```

Get your keys from:
- Groq: https://console.groq.com
- OpenWeatherMap: https://openweathermap.org/api

### 4. Run the app

```bash
streamlit run app.py
```

---

## How It Works

```
User message
     ↓
Step 1 — LLM decides if weather tool is needed (auto)
     ↓
Step 2 — Geocoding API resolves city name → lat/lon (handles typos)
     ↓
Step 3 — OpenWeatherMap fetches weather by coordinates
     ↓
Step 4 — LLM generates a natural language response using weather data + conversation history
```

For follow-up questions (no new city mentioned), the last fetched weather data is injected into context so the bot doesn't lose track of the conversation.

---

## Example Conversations

**Basic weather query:**
> User: What's the weather in Tokyo?
> Bot: Tokyo is currently clear at 22°C, feeling like 21°C, with humidity at 58% and light winds...

**Activity planning:**
> User: I'm planning an outdoor wedding in Kochi. Any suggestions?
> Bot: Based on current conditions in Kochi — 32°C, broken clouds, humidity at 74%...

**Typo handling:**
> User: Weather in Landan?
> Bot: Showing weather for London, England, GB (closest match to 'Landan')...

**Follow-up:**
> User: Suggest a specific venue there
> Bot: *(remembers Kochi + wedding context)* Based on the clear skies and warm conditions...

---

## Limitations

- Very small towns and villages (e.g. Athirappally) may not be in OpenWeatherMap's database — the bot will ask you to try a nearby larger city
- Weather context resets when the Streamlit session is refreshed
- Free OpenWeatherMap plan allows 60 calls/minute
