# SchemaSculpt 🗿

An intelligent, AI-powered assistant for crafting perfect API specifications. SchemaSculpt goes beyond simple validation, providing smart suggestions, one-click fixes, and a clear path towards an AI-native development experience.



## About The Project

Writing and maintaining OpenAPI specifications can be tedious. It's easy to make mistakes, leave unused components lying around, or forget best practices. SchemaSculpt was built to solve this problem.

It started as a high-performance validator and linter but is architected from the ground up to become a true AI partner for API design. The goal is to leverage modern AI to provide deeper insights, automate tedious tasks, and help developers create high-quality, secure, and intuitive APIs with less effort.

## Key Features

* **⚡ Real-time Validation**: Instantly see parsing and validation errors as you type.
* **💡 Intelligent Suggestions (Linter)**: Get smart suggestions that go beyond basic validation, such as finding unused components or operations missing summaries.
* **🪄 One-Click Quick Fixes**: Automatically fix suggestions with the click of a button, letting the tool do the work for you.
* **👁️ Live Swagger UI Visualization**: Instantly see your API rendered in a beautiful, interactive documentation panel.
* **🔄 JSON <> YAML Conversion**: Seamlessly write in and convert between JSON and YAML formats with a single click.
* **✨ Modern UI**: A clean, professional, and resizable split-pane view that feels like a modern IDE.

## Tech Stack

| Frontend | Backend |
| :--- | :--- |
| React | Java 21 |
| Monaco Editor | Spring Boot 3 |
| `react-resizable-panels` | Maven |
| `swagger-ui-react` | `swagger-parser` |
| `axios` & `js-yaml` | JUnit 5 |

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

* Java 21 (or higher)
* Node.js and npm

### Local Setup

1.  **Clone the repo**
    ```sh
    git clone [https://github.com/sharma-manish-94/schemasculpt.git](https://github.com/sharma-manish-94/schemasculpt.git)
    ```
2.  **Run the Backend**
    ```sh
    cd schemasculpt/api
    ./mvnw spring-boot:run
    ```
    The backend will start on `http://localhost:8080`.

3.  **Run the Frontend** (in a new terminal window)
    ```sh
    cd schemasculpt/ui
    npm install
    npm start
    ```
    The frontend will start on `http://localhost:3000`.

4.  **Open the App**
    Open your browser and navigate to `http://localhost:3000`.

## 🚀 The Vision: The Road to an AI-Native API Editor

The current features are just the foundation. The ultimate goal for SchemaSculpt is to integrate powerful AI capabilities to revolutionize API design. The roadmap includes:

* **Natural Language to Spec**: Describe an endpoint in plain English ("Create a POST endpoint to add a new user with an email and name") and have the AI generate the corresponding YAML/JSON.
* **Semantic Refactoring**: AI-powered suggestions to simplify overly complex schemas or refactor API paths to better align with RESTful best practices.
* **Automated Documentation**: AI-generated `summary` and `description` fields based on the endpoint's structure, parameters, and schema names.
* **Advanced Security Audits**: Using AI to detect subtle security vulnerabilities in the API design, such as potential for data leakage or improper authentication schemes.

## Contributing

The kitchen is a bit of a mess right now, and the chef (that's me) is still trying to perfect the recipe. To avoid any unexpected explosions of code, I'm not accepting contributions just yet.

However, feel free to open an issue to share ideas or report bugs!

## License

This digital territory is currently an independent sovereignty with a benevolent dictator. A formal constitution (i.e., a license) is forthcoming.

Until then, all rights are reserved.

