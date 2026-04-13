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

# --- UI ---
st.set_page_config(page_title="AI Weather Planner", page_icon="⛅")
st.title("🤖 Agentic Weather Planner ⛅")

if "messages" not in st.session_state:
    st.session_state.messages = []

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
                # --- STEP 1: FORCE TOOL CALL ---
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a STRICT weather assistant.\n"
                                "For ANY user query that mentions a place (even indirectly like travel, cycling, trip), "
                                "you MUST call get_weather.\n"
                                "You MUST NOT answer using your general knowledge on the weather of that place.\n"
                                "You MUST ONLY use the tool response to generate your answer along with your general knowledge."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ],
                    tools=tools,
                    tool_choice={
                        "type": "function",
                        "function": {"name": "get_weather"}
                    }
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                if tool_calls:
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        args = tool_call.function.arguments

                        # If it's a string → parse it
                        if isinstance(args, str):
                            args = json.loads(args)

                        city = args.get("city")

                        # --- SAFETY CHECK ---
                        if not city or len(city) < 2:
                            ans_text = "⚠️ Couldn't detect location properly."
                            break

                        status.update(
                            label=f"🔧 Getting real weather for {city}...",
                            state="running"
                        )

                        # --- STEP 2: CALL WEATHER API ---
                        weather_info = get_weather(city)

                        # --- STEP 3: FINAL RESPONSE ---
                        final_response = client.chat.completions.create(
                            model=MODEL_ID,
                            messages=[
                                {
                                    "role": "system",                      
                                    "content": (
                                        "Answer ONLY using the provided weather data. "
                                        "Do NOT use general seasonal knowledge. "
                                        "Give practical advice based on current conditions."
                                    )
                                },
                                {"role": "user", "content": prompt},
                                response_message,
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": function_name,
                                    "content": json.dumps(weather_info),
                                },
                            ],
                        )

                        ans_text = final_response.choices[0].message.content

                else:
                    ans_text = "⚠️ No weather data retrieved."

                status.update(label="✅ Done", state="complete")

            except Exception as e:
                status.update(label="❌ Error", state="error")
                ans_text = f"Error: {str(e)}"

        st.markdown(ans_text)
        st.session_state.messages.append({"role": "assistant", "content": ans_text})