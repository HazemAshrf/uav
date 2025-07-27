"""Configuration settings for the UAV design system."""

import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# API Configuration
openai_api_key = os.getenv("OPENAI_API_KEY")

# Model Configuration
MODEL_NAME = "gpt-4o-mini"

# System Configuration
MAX_ITERATIONS = 20
STABILITY_THRESHOLD = 3

# Agent Communication Rules
COMMUNICATION_RULES = {
    "mission_planner": ["aerodynamics", "propulsion", "structures"],
    "aerodynamics": ["mission_planner", "propulsion", "structures"],
    "propulsion": ["mission_planner", "aerodynamics"],
    "structures": ["mission_planner", "aerodynamics", "manufacturing"],
    "manufacturing": ["structures"]
}

# Initialize LLM
def get_llm() -> ChatOpenAI:
    """Get configured LLM instance using GPT-4o mini."""
    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=openai_api_key,
        temperature=0.1,
        max_retries=3
    )