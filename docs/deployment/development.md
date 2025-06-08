# Development Environment Setup

Follow these steps to run the project locally for development.

1. Clone the repository and create a Python virtual environment:
   ```bash
   git clone https://github.com/All-About-AI-YouTube/ai_video_pipeline.git
   cd ai_video_pipeline
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set API keys and configuration values.
3. Start the services with Docker Compose:
   ```bash
   docker compose up -d
   ```
4. Run tests to ensure everything works:
   ```bash
   pytest
   ```

Environment variables should always be validated before use. See `AGENTS.md` for development standards.
