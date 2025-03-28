# AI Travel Planner

An AI-powered travel planner application that assists travelers in creating personalized itineraries based on their preferences.

## Features

- Collects user travel preferences including budget, duration, destination, and more
- Refines user inputs through conversational AI
- Searches the web for up-to-date travel suggestions using Tavily API
- Generates personalized activity suggestions based on user preferences
- Creates detailed day-by-day itineraries
- Allows downloading of the final itinerary as a text file

## Tech Stack

- **Frontend/Backend**: Streamlit
- **LLM**: Google Gemini 1.5 Flash
- **Web Search**: Tavily API
- **Environment Management**: dotenv

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd travel-planner
   ```

2. **Install the required dependencies**:
   ```
   pip install -r requirements.txt
   ```

3. **Set up API keys**:
   - Create a `.env` file in the root directory based on the `.env.example` template
   - Add your Google API key for Gemini access
   - Add your Tavily API key for web search capabilities

4. **Run the application**:
   ```
   streamlit run app.py
   ```

## Usage

1. **Enter Initial Travel Details**: Fill out the form with your travel preferences, including budget, duration, destination, and more.

2. **Refine Your Preferences**: Engage in a conversation with the AI to provide more details and clarify your preferences.

3. **Review Suggestions**: The AI will search the web and provide personalized activity suggestions based on your preferences. You can approve these or request modifications.

4. **Get Your Itinerary**: After approving the suggestions, the AI will generate a detailed day-by-day itinerary, which you can review and download.

## Obtaining API Keys

- **Google Gemini API**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey) to create an API key.
- **Tavily API**: Sign up at [Tavily](https://tavily.com/) to get your API key.

