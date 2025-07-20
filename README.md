# Route Trace API

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg) ![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg) ![Database](https://img.shields.io/badge/Database-SQLAlchemy-red.svg) ![License](https://img.shields.io/badge/license-MIT-blue.svg)

The **Route Trace API** is a powerful and intelligent network analysis tool designed to provide detailed, end-to-end network path tracing. Built with Python and FastAPI, it goes beyond a simple `traceroute` by integrating with your entire network ecosystem, including a Trino datalake, Tufin SecureTrack, and live network devices, to provide a comprehensive view of both Layer 2 and Layer 3 paths.

---

## 🚀 Key Features

*   **Hybrid Data Sourcing**: Combines real-time data from network devices (Cisco, Checkpoint) with historical data from a Trino datalake and topology information from Tufin for maximum accuracy.
*   **End-to-End Path Analysis**: Performs both Layer 2 (MAC-based) and Layer 3 (IP-based) tracing to give a complete picture of the network path.
*   **Intelligent Parsing**: Leverages an external AI service to dynamically parse unstructured text output from device commands, ensuring compatibility and robustness.
*   **Firewall & MPLS Awareness**: Intelligently handles complex network scenarios, including Checkpoint firewalls, MPLS labels, and Traffic-Engineered tunnels.
*   **RESTful & Asynchronous**: A modern API built on FastAPI, offering high performance and automatic interactive documentation (via Swagger UI).
*   **Persistent History**: Saves every trace to a database, creating a searchable history of network paths that can be reviewed and analyzed.
*   **Secure**: Protects endpoints using JWT-based authentication, with a clever mechanism that validates credentials against live network devices.

---

## 🏛️ Architecture Overview

The application is designed with a modular architecture that separates concerns, making it scalable and easy to maintain.

1.  **FastAPI Core (`app.py`)**: The main entry point that serves the API. It includes all the routers that define the available endpoints.
2.  **API Routers (`/routers`)**: Defines all API endpoints for authentication, route tracing, and historical data retrieval. It handles request validation and authentication checks.
3.  **The Tracer (`/tracer`)**: This is the brain of the operation. The `Tracer` class orchestrates the entire tracing process. It decides whether to query the datalake, connect to a live device, or consult Tufin based on the current hop's context.
4.  **Data Sources**:
    *   **Trino Datalake (`/tracer/routetrace/FromDatabase.py`)**: Used as the primary source for historical network state, such as ARP tables, CDP neighbors, and interface configurations. This reduces the load on live devices.
    *   **Live Devices (`/tracer/routetrace/FromDevices.py`)**: When real-time information is needed, the tracer connects directly to switches, routers, and firewalls using Paramiko (for Cisco) and Netmiko (for Checkpoint).
    *   **Tufin SecureTrack (`/Tufin/Tufin.py`)**: Used to query firewall topology and understand routing through complex firewall policies.
5.  **Database (`/database`)**: Uses SQLAlchemy to interact with a database (configured for MySQL). It stores user information and every route trace result for historical analysis.
6.  **AI Parser (`/AI_parser`)**: A client that sends raw text from device commands to an external microservice, which returns structured data. This makes the tool adaptable to different OS versions and command outputs.

---

## 🔧 Setup & Installation

Follow these steps to get the Route Trace API running in your environment.

### Prerequisites

*   Python 3.9+
*   Access to a MySQL database (or modify `database/models.py` for another backend like SQLite).
*   Network connectivity to your Trino Datalake, Tufin instance, network devices, and the AI Parser service.

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd route-trace-api