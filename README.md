<a name="readme-top"></a>

<div align="center">
  <img src="https://cdn.prod.website-files.com/66a1237564b8afdc9767dd3d/66df7b326efdddf8c1af9dbb_Momentum%20Logo.svg" height="80">
  <h1>Apple Health MCP Server</h1>
  <p><strong>Apple Health Data Exploration</strong></p>

  [![Contact us](https://img.shields.io/badge/Contact%20us-AFF476.svg?style=for-the-badge&logo=mail&logoColor=black)](mailto:hello@themomentum.ai?subject=Apple%20Health%20MCP%20Server%20Inquiry)
  [![Visit Momentum](https://img.shields.io/badge/Visit%20Momentum-1f6ff9.svg?style=for-the-badge&logo=safari&logoColor=white)](https://themomentum.ai)
  [![MIT License](https://img.shields.io/badge/License-MIT-636f5a.svg?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)

  <a href="https://glama.ai/mcp/servers/@the-momentum/apple-health-mcp-server">
    <img width="380" height="200" src="https://glama.ai/mcp/servers/@the-momentum/apple-health-mcp-server/badge" alt="Apple Health Server MCP server" />
  </a>
</div>

> [!NOTE]
> **This project has evolved into [Open Wearables](https://github.com/the-momentum/open-wearables)** - self-hosted platform to unify wearable health data from multiple devices, including Apple Health. Open Wearables also provides an MCP server and a companion app for continuous Apple Health data sync, eliminating the need for manual XML exports. Check it out: [github.com/the-momentum/open-wearables](https://github.com/the-momentum/open-wearables)

---
Connect your Apple Health data with any LLM that supports MCP. Talk to your data and get personalised insights.

## 💡 Demo

This demo shows how Claude uses the `apple-health-mcp-server` to answer questions about your data. Example prompts from the demo:
- I would like you to help me analyze my Apple Health data. Let's start by analyzing the data types - check what data is available and how much of it there is.
- What can you tell me about my activity in the last week? How did my daily statistics look?
- Please also summarise my running workouts in July and June. Do you see anything interesting?

https://github.com/user-attachments/assets/93ddbfb9-6da9-42c1-9872-815abce7e918


Want to try it out? **[🚀 Getting Started](docs/getting-started.md)**

## 🌟 Why to use Apple Health MCP Server?

 - **🧩 Fit your data everywhere**: using this software you can import data exported from Apple devices into any DBMS, base importer is already prepared for extensions
 - **🎯 Simplify complex data access**: you don't need to know data structure or use any structured query language, like SQL, simple access is just granted with natural language
 - **🔍︎ Find hidden trends**: use LLM as a gate to flexible auto-generated queries which will be able to find data trends not so easy to detect manually

## ✨ Key Features

- **🚀 FastMCP Framework**: Built on FastMCP for high-performance MCP server capabilities
- **🍏 Apple Health Data Exploration**: Import, parse, and analyze Apple Health XML exports
- **🔎 Powerful Search & Filtering**: Query and filter health records using natural language and advanced parameters
- **📦 Elasticsearch, ClickHouse or DuckDB Integration**: Index and search health data efficiently at scale
- **🛠️ Modular MCP Tools**: Tools for structure analysis, record search, type-based extraction, and more
- **📈 Data Summaries & Trends**: Generate statistics and trend analyses from your health data
- **🐳 Container Ready**: Docker support for easy deployment and scaling
- **🔧 Configurable**: Extensive ```.env```-based configuration options

## 📚 Documentation

- **[🚀 Getting Started](docs/getting-started.md)** - Complete setup guide
- **[🔍 About](docs/about.md)** - Detailed description & architecture
- **[🔧 Configuration](docs/configuration.md)** - Environment variables and settings
- **[🛠️ MCP Tools](docs/mcp-tools.md)** - All available tools
- **[🗺️ Roadmap](docs/roadmap.md)** - Upcoming features and roadmap

**Need help?** Looking for guidance on use cases or implementation? Don't hesitate to ask your question in our [GitHub discussion forum](https://github.com/the-momentum/apple-health-mcp-server/discussions)! You'll also find interesting use cases, tips, and community insights there.

## 👥 Contributors

<a href="https://github.com/the-momentum/apple-health-mcp-server/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=the-momentum/apple-health-mcp-server" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 💼 About Momentum
This project is part of Momentum’s open-source ecosystem, where we make healthcare technology more secure, interoperable, and AI-ready. Our goal is to help HealthTech teams adopt standards such as FHIR safely and efficiently. We are healthcare AI development experts, recognized by FT1000, Deloitte Fast 50, and Forbes for building scalable, HIPAA-compliant solutions that power next-generation healthcare innovation.

📖 Want to learn from our experience? Read our insights → <a href="https://www.themomentum.ai/blog">themomentum.ai/blog</a>. 
Interested? <a href="http://themomentum.ai/lets-talk">Let's talk</a>!

<div align="center">
  <p><em>Built with ❤️ by <a href="https://themomentum.ai">Momentum</a> • Transforming healthcare data management with AI</em></p>
</div>
