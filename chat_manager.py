import requests
from autogen import ConversableAgent, AssistantAgent, GroupChat, GroupChatManager
import autogen

# === Weather Data Fetching Function ===
def get_weather_data(city="London"):
    api_key = "8d849d66f3a9a56d9b5fb30b35ec5a32"  # Replace this with your actual key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return f"Error fetching data: {data.get('message', 'Unknown error')}"

    return {
        "location": city,
        "temperature_c": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "wind_kph": data["wind"]["speed"] * 3.6,  # convert m/s to km/h
        "condition": data["weather"][0]["description"].title()
    }

# === LLM Configuration for Mistral 7B hosted via LM Studio ===
llm_config = {
    "config_list": [
        {
            "model": "mistral-7b-instruct-v0.1",
            "api_key": "NULL",  # Not used locally
            "base_url": "http://localhost:1234/v1",
            "api_type": "openai",
            "price": [0, 0]  # Optional to suppress pricing warnings
        }
    ],
    "temperature": 0.7,
    "cache_seed": 42,
    "timeout": 120,
}

# === Trigger Agent ===
trigger_agent = ConversableAgent(
    name="TriggerAgent",
    system_message="You are responsible for triggering the CMHS monitoring cycle. Initiate by asking EnvParamAgent to fetch weather data.",
    llm_config=llm_config,
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=5,
)

# === Environmental Parameter Agent ===
env_agent = AssistantAgent(
    name="EnvParamAgent",
    system_message=(
        "You are responsible for collecting current weather data using the OpenWeatherMap API. "
        "Fetch temperature, humidity, wind speed, and condition for the city 'London'. "
        "Return this information in a JSON-like format."
    ),
    llm_config=llm_config,
    code_execution_config={"use_docker": False}
)

# Agent's task of collecting weather data
def collect_weather_data():
    city = "London"  # You can customize this to any city
    weather_data = get_weather_data(city)
    return weather_data

# === Group Chat Manager ===
groupchat = GroupChat(
    agents=[trigger_agent, env_agent],
    messages=[],
    max_round=10,
    speaker_selection_method="round_robin",  # Prevent repeating same agent
    allow_repeat_speaker=False,  # Prevent repeating speaker
)

chat_manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

# === Start the conversation ===
trigger_agent.initiate_chat(chat_manager, message="Please collect weather data for London and share the key parameters.")
