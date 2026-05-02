# Hitachi AI Advisor
The main repository for the Hitachi AI Advisor microservices ecosystem.

## Overview
This project orchestrates the various microservices that power the AI Advisor. It uses Docker Compose to ensure a consistent environment across development and deployment.

## Prerequisites
* **Docker** (v20.10+)
* **Docker Compose**
* A public-facing IP (for Webhook integration)

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd hitachi-ai-advisor

1. **Launch the services:**
   ```bash
   docker compose up --build

1. **Open a tunnel using localhost.run**
   ```bash
   ssh -R 80:localhost:3000 localhost.run

1. **You are now ready to receive webhooks on address_assigned_by_localhost.run/webhook**