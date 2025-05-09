# 4. Communication Architecture: Spring Boot & FastAPI via RabbitMQ

This document outlines the asynchronous communication architecture between the Spring Boot main backend and the FastAPI multi-agent backend, utilizing RabbitMQ as a message broker and Celery for task management within FastAPI.

## 1. Overview

To handle potentially long-running AI agent tasks (30 seconds to 1+ minute) initiated by the Spring Boot backend, an asynchronous communication pattern is employed. This ensures that the Spring Boot application remains responsive and is decoupled from the processing time of the FastAPI agent system. RabbitMQ serves as the central message bus.

## 2. Core Components

- **Spring Boot Application (Producer/Consumer):**

  - Acts as a **Producer** when it needs to delegate a task to the FastAPI multi-agent system. It sends a "task" message to a RabbitMQ queue.
  - Acts as a **Consumer** when it listens for "result" messages from a RabbitMQ queue, which contain the outcomes of the processed agent tasks.

- **RabbitMQ (Message Broker):**

  - The intermediary that decouples Spring Boot from FastAPI.
  - Manages queues for tasks and results, ensuring reliable message delivery.
  - Key queues (example names):
    - `agent_tasks_queue`: For messages from Spring Boot to FastAPI.
    - `agent_results_queue`: For messages from FastAPI back to Spring Boot.

- **FastAPI Application with Celery (Consumer/Producer):**
  - **Celery Workers** act as **Consumers** by listening to the `agent_tasks_queue`. When a message arrives, a worker picks it up and executes the corresponding multi-agent logic.
  - After processing is complete, the Celery worker acts as a **Producer** by sending a "result" message (containing the outcome) to the `agent_results_queue`.

## 3. Message Flow

The communication follows these steps:

1.  **Task Submission:**

    - An event occurs in the Spring Boot application (e.g., triggered by a frontend request) that requires processing by the AI agents.
    - Spring Boot constructs a "task" message. This message contains all necessary information for the FastAPI service to execute the agent logic (e.g., query, user ID, data context).
    - Spring Boot publishes this "task" message to the `agent_tasks_queue` in RabbitMQ.
    - Spring Boot can then immediately acknowledge the initial request (e.g., to the frontend) with a "processing started" status, possibly including a task ID for later correlation.

2.  **Task Processing (FastAPI & Celery):**

    - Celery workers, running as part of the FastAPI service, are continuously listening to the `agent_tasks_queue`.
    - One of the available Celery workers picks up a "task" message from the queue.
    - The worker deserializes the message and executes the defined multi-agent business logic. This is where the potentially long-running inter-agent communication and processing occur.

3.  **Result Publication (FastAPI & Celery):**

    - Once the multi-agent task is complete, the Celery worker constructs a "result" message. This message contains the outcome of the processing (e.g., generated text, analysis data, success/failure status).
    - The Celery worker publishes this "result" message to the `agent_results_queue` in RabbitMQ.

4.  **Result Consumption (Spring Boot):**
    - The Spring Boot application has listeners configured for the `agent_results_queue`.
    - When a "result" message arrives, Spring Boot consumes it.
    - It can then process this result: update a database, notify the user/frontend (e.g., via WebSockets or by allowing the frontend to poll for results associated with a task ID), or trigger further actions.

## 4. Message Data Format

- Messages exchanged via RabbitMQ will typically be in JSON format.
- The structure of these JSON payloads (both for "tasks" and "results") should be clearly defined and agreed upon.
- Within the FastAPI application, Pydantic models will be used to validate the structure of incoming "task" messages and to construct outgoing "result" messages, ensuring data integrity.

## 5. Benefits of this Architecture

- **Decoupling:** Spring Boot and FastAPI are not directly dependent on each other's immediate availability. Spring Boot can send a task even if FastAPI workers are temporarily busy or restarting.
- **Scalability:** The number of FastAPI Celery workers can be scaled independently based on the load in the `agent_tasks_queue`, without affecting the Spring Boot application.
- **Resilience & Fault Tolerance:** Messages remain in RabbitMQ if a consuming service is down, and can be processed once the service recovers. This prevents data loss. For long-running tasks, this prevents timeouts that would occur with synchronous HTTP communication.
- **Improved Responsiveness:** Spring Boot can respond quickly to initial requests, as it doesn't have to wait for the full agent processing to complete.

This asynchronous architecture provides a robust foundation for communication between your Spring Boot and FastAPI services, especially considering the duration of the agent tasks.
