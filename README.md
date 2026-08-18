Nexus AI Gateway

«An intelligent, provider-agnostic AI gateway that automatically discovers AI models and routes requests based on capabilities, performance, health, and policy.»

Nexus AI Gateway provides a unified API for AI-powered applications while abstracting away provider-specific implementations. It discovers available models, normalises their capabilities, and intelligently selects the most suitable model for each request.

Features

- Provider-agnostic architecture
- Automatic model discovery
- Capability-based routing
- Anthropic-compatible API
- OpenAI-compatible API
- Streaming support
- Health-aware failover
- Configurable routing policies
- Extensible provider framework
- Production-ready FastAPI foundation

Provider Availability

The gateway is designed to support multiple AI providers through a common abstraction layer.

| Provider | Status |
| :--- | :--- |
| LiteLLM | Implemented |
| Ollama | Implemented |
| DashScope | Planned / Not Implemented |
| Gemini | Planned / Not Implemented |
| Mistral | Planned / Not Implemented |
| OpenRouter | Planned / Not Implemented |
| DeepSeek | Planned / Not Implemented |

Additional providers can be added without modifying the routing engine.

Quick Start

Clone the repository

git clone https://github.com/<your-org>/nexus-ai-gateway.git
cd nexus-ai-gateway

Create a virtual environment

python -m venv .venv

Activate the environment

Linux/macOS:

source .venv/bin/activate

Install dependencies

pip install -r requirements.txt

Configure environment variables

cp .env.example .env

Update the required provider credentials in ".env".

Run the server

uvicorn app.main:app --reload

The API will be available at:

http://127.0.0.1:8000

Configuration

Provider configuration:

config/providers.yaml

Routing policies:

config/router.yaml

Environment variables:

.env

API Endpoints

Endpoint| Description
"GET /health"| Health check
"GET /metrics"| Service metrics
"GET /v1/models"| Available models
"POST /v1/messages"| Anthropic-compatible API
"POST /v1/chat/completions"| OpenAI-compatible API

Documentation

Additional documentation is available in the "docs/" directory:

- Architecture
- Routing
- Provider integrations
- Model discovery
- Deployment
- Contributing
- Benchmarking
- Roadmap

Contributing

Contributions are welcome.

Please open an issue to discuss significant changes before submitting a pull request.

Licence

Released under the MIT License.
