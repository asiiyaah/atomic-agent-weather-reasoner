import streamlit as st
import os
import json
from dotenv import load_dotenv
from tools import get_weather
from groq import Groq

load_dotenv()

# --- CONFIG ---
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_ID = "llama-3.1-8b-instant"

# --- TOOL DEFINITION ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a specific city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name like Tokyo, London, Paris",
                    }
                },
                "required": ["city"],
            },
        },
    }
]

# --- HELPER: Safely extract city from tool call args ---
def extract_city(args):
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return None
    if "city" in args:
        return args["city"]
    if "parameters" in args and isinstance(args["parameters"], dict):
        return args["parameters"].get("city")
    return None

# --- UI ---
st.set_page_config(page_title="AI Weather Planner", page_icon="⛅")
st.title("🤖 Agentic Weather Planner ⛅")

if "messages" not in st.session_state:
    st.session_state.messages = []

# last_weather_context stores the most recent weather data fetched
# so follow-up questions can reference it without re-fetching
if "last_weather_context" not in st.session_state:
    st.session_state.last_weather_context = None

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- MAIN LOOP ---
if prompt := st.chat_input("Ask about weather anywhere..."):

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Agent thinking...") as status:

            try:
                # --- STEP 1: DECIDE IF TOOL CALL NEEDED ---
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a weather assistant.\n"
                                "If the user query is about weather OR mentions a place in the context of an activity "
                                "(travel, trip, cycling, visiting, going somewhere, event planning), call get_weather for that place.\n"
                                "If the query is a follow-up question with no new location mentioned, do NOT call the tool.\n"
                                "You MUST NOT answer using your general knowledge about weather.\n"
                                "Always extract just the city/place name to pass to get_weather."
                            )
                        },
                        *st.session_state.messages,
                    ],
                    tools=tools,
                    tool_choice="auto"
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                if tool_calls:
                    for tool_call in tool_calls:
                        city = extract_city(tool_call.function.arguments)

                        if not city or len(city) < 2:
                            ans_text = "⚠️ Couldn't detect location properly. Please mention a city name."
                            break

                        status.update(
                            label=f"🔧 Getting real weather for {city}...",
                            state="running"
                        )

                        # --- STEP 2: CALL WEATHER API ---
                        weather_info = get_weather(city)

                        # Save weather context for follow-up questions
                        st.session_state.last_weather_context = {
                            "city": city,
                            "data": weather_info
                        }

                        # --- STEP 3: FINAL RESPONSE ---
                        final_response = client.chat.completions.create(
                            model=MODEL_ID,
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "You are a helpful weather assistant with memory of the conversation. "
                                        "Answer ONLY using the provided weather data. "
                                        "Do NOT use general seasonal knowledge. "
                                        "Give a complete and helpful weather description including temperature, feels like, "
                                        "humidity, wind, rain, and conditions. "
                                        "Answer exactly what the user asked. "
                                        "Only give travel or activity advice if the user explicitly asked for it. "
                                        "NEVER show raw JSON or data structures in your response. "
                                        "ALWAYS present weather information in clean, natural, human-readable sentences."
                                    )
                                },
                                *st.session_state.messages,
                                response_message,
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": tool_call.function.name,
                                    "content": json.dumps(weather_info),
                                },
                            ],
                        )

                        ans_text = final_response.choices[0].message.content

                else:
                    # No new tool call — use last weather context for follow-up answers
                    extra_context = ""
                    if st.session_state.last_weather_context:
                        extra_context = (
                            f"\n\nFor reference, the last weather data fetched was for "
                            f"{st.session_state.last_weather_context['city']}: "
                            f"{json.dumps(st.session_state.last_weather_context['data'])}"
                        )

                    followup_response = client.chat.completions.create(
                        model=MODEL_ID,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are a helpful weather assistant with memory of the conversation. "
                                    "Use the conversation history and the last weather data provided to answer follow-up questions. "
                                    "Do NOT fabricate new weather data. "
                                    "NEVER show raw JSON. "
                                    "ALWAYS respond in clean, natural, human-readable sentences."
                                    + extra_context
                                )
                            },
                            *st.session_state.messages,
                        ],
                    )
                    ans_text = followup_response.content or followup_response.choices[0].message.content

                status.update(label="✅ Done", state="complete")

            except Exception as e:
                status.update(label="❌ Error", state="error")
                ans_text = f"Error: {str(e)}"

        st.markdown(ans_text)
        st.session_state.messages.append({"role": "assistant", "content": ans_text})