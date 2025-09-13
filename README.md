# SchemaSculpt 🗿

### Your AI Co-pilot for Flawless APIs

SchemaSculpt is an intelligent, locally-run assistant for crafting perfect API specifications. It goes beyond simple validation by providing smart suggestions, one-click fixes, and AI-powered editing to streamline your API design workflow.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/License-All_Rights_Reserved-red)


![SchemaSculpt Demo](./assets/editor.gif)

## About The Project

Writing and maintaining OpenAPI specifications can be tedious. It's easy to make mistakes, leave unused components lying around, or forget best practices. SchemaSculpt was built to solve this problem by acting as your AI partner for API design.

It uses a powerful, locally-run LLM (via Ollama) to understand natural language commands, allowing you to edit and extend your API specs just by having a conversation. The built-in linter and quick-fix engine help you adhere to best practices and keep your specifications clean and maintainable.

## Key Features

* **🤖 AI-Powered Editing**: Use natural language prompts (e.g., "add a GET endpoint for /health") to have a local LLM modify your API specification.
* **⚡ Real-time Validation**: Instantly see parsing and OpenAPI validation errors as you type.
* **💡 Intelligent Linter**: Get smart suggestions that go beyond basic validation, including:
    * Detecting unused component schemas.
    * Flagging operations with missing `summaries` or `tags`.
    * Enforcing `PascalCase` naming conventions for schemas.
    * Finding operations with a missing `operationId`.
* **🪄 One-Click Quick Fixes**: Automatically fix linter suggestions—like removing unused components or generating a missing `operationId`—with the click of a button.
* **👁️ Live Swagger UI Visualization**: Instantly see your API rendered in a beautiful, interactive documentation panel in a separate tab.
* **🔄 JSON <> YAML Conversion**: Seamlessly write in and convert between JSON and YAML formats with a single click.
* **✨ Modern UI**: A clean, professional, and resizable split-pane view that feels like a modern IDE.

## Tech Stack

| Frontend | Backend (API Gateway) | Backend (AI Service) |
| :--- | :--- | :--- |
| React | Java 21 | Python 3 |
| Monaco Editor | Spring Boot 3 | FastAPI |
| `react-resizable-panels` | Maven | Ollama |
| `swagger-ui-react` | `swagger-parser` | |
| `axios` & `js-yaml` | JUnit 5 | |

## Getting Started

To get the full local environment running, you'll need to start the AI model, the Python AI service, the Java backend, and the React frontend.

### Prerequisites

* Java 21 (or higher)
* Python 3.10+
* Node.js and npm
* **Ollama**: Download and install from [ollama.com](https://ollama.com)

### Local Setup

1.  **Clone the repo**
    ```sh
    git clone [https://github.com/sharma-manish-94/schemasculpt.git](https://github.com/sharma-manish-94/schemasculpt.git)
    cd schemasculpt
    ```
2.  **Run the Local AI Model** (in a new terminal)
    * First, pull the model:
        ```sh
        ollama pull mistral
        ```
    * Ollama runs as a background service, so you just need to ensure it's active.

3.  **Run the Python AI Service** (in a new terminal)
    ```sh
    cd ai_service
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt  # (You may need to create a requirements.txt)
    uvicorn main:app --reload
    ```
    The AI service will start on `http://localhost:8000`.

4.  **Run the Java Backend** (in a new terminal)
    ```sh
    cd api
    ./mvnw spring-boot:run
    ```
    The backend will start on `http://localhost:8080`.

5.  **Run the React Frontend** (in a new terminal)
    ```sh
    cd ui
    npm install
    npm start
    ```
    The frontend will start on `http://localhost:3000`.

6.  **Open the App**
    Open your browser and navigate to `http://localhost:3000`. The full application should now be running.

## 🚀 Future Roadmap

The current AI features are just the beginning. The vision is to continue making SchemaSculpt a more powerful AI-native tool:
* **AI-Powered Quick Fixes**: Enable the AI to suggest and perform more complex fixes and refactors.
* **Automated Documentation**: Generate high-quality `summary` and `description` fields for all parts of the spec.
* **Semantic Refactoring**: Suggest deeper improvements, like refactoring API paths for better RESTful practices.
* **Test Generation**: Generate boilerplate API tests based on the specification.

## Contributing

The kitchen is a bit of a mess right now, and the chef (that's me) is still trying to perfect the recipe. To avoid any unexpected explosions of code, I'm not accepting contributions just yet.

However, feel free to open an issue to share ideas or report bugs!

## License

This digital territory is currently an independent sovereignty with a benevolent dictator. A formal constitution (i.e., a license) is forthcoming.

Until then, all rights are reserved.
