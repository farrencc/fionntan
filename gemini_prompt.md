Fionntán is a research paper podcast generator designed to convert academic papers from ArXiv into engaging, conversational audio podcasts.

Project Description:

The application's backend is built with Python using Flask for the API, SQLAlchemy for database interaction with PostgreSQL, and Celery for managing background tasks like script and audio generation. It integrates with several Google Cloud services: the ArXiv API for fetching paper metadata, the Gemini API for generating conversational scripts, Google Cloud Text-to-Speech (TTS) for creating audio from the scripts, and Google Cloud Storage for storing the final audio files. The frontend is a React application that provides a user interface for managing preferences, creating podcasts, and playing the generated audio. User authentication is handled via Google OAuth, with JWTs for securing API endpoints.

Progress So Far:

    Backend: The core backend infrastructure is largely in place. This includes:
        User authentication with Google OAuth and JWT management.
        Database models for users, preferences, podcasts, and generation tasks.
        A service layer for interacting with external APIs (ArXiv, Gemini, TTS, Storage).
        Celery tasks to handle the asynchronous generation of scripts and audio.
        A comprehensive suite of pytest tests that mock external services to verify the application's logic and flow.
        A CI/CD pipeline using GitHub Actions to run tests and build Docker images.
    Frontend: The basic structure for the user interface has been created using React and Material-UI. Core pages and components exist for:
        Login, Dashboard, User Preferences, Podcast Creation, Podcast Listing, and a detailed Podcast View with an audio player.
    Integration: Initial debugging and connection between the frontend and backend have begun, and the ArXiv scraping functionality has been successfully tested. The TTS service has been updated to use Google's advanced "Chirp 3 HD" voices to improve the naturalness of the audio.

Future Goals & Immediate Focus:

    Improve Conversational Nature of Podcasts (Highest Priority): The primary goal is to make the generated audio sound less robotic and more like a natural conversation. This involves:
        Leveraging the newly selected "Chirp 3 HD" voices.
        Significantly enhancing the use of SSML (Speech Synthesis Markup Language) to control prosody (rate, pitch, volume), emphasis, and strategic pauses.
        Refining the prompts sent to the Gemini API to request more conversational script outputs.

    Complete Frontend-Backend Integration & UX Refinement (High Priority):
        Systematically test and ensure all existing user flows are fully functional.
        Resolve any outstanding issues in request/response handling between the React and Flask applications.
        Implement robust frontend loading states (e.g., progress bars, spinners) and user-friendly error notifications.

    Implement Paper Discovery/Access (Medium Priority):
        Enhance the UI (likely on the Podcast Detail page) to make it easy for users to find and access the source ArXiv papers that a podcast is based on, for instance, by providing prominent links to the paper's abstract page.