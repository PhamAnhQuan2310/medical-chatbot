# Medical Chatbot

A web-based chatbot developed as a university project to support healthcare information lookup and internal hospital data retrieval.

The system includes a medical question-answering chatbot for users and a separate workflow for hospital staff to search structured and document-based data.

## Main Features

- Medical question answering using a fine-tuned Qwen-2.5-0.5B-Instruct model.
- RAG-based retrieval for document data using ChromaDB.
- Query structured datasets and return results as tables or charts.
- Upload and manage documents used by the internal chatbot.
- Speech-to-Text input through the browser microphone.
- OCR input for extracting text from uploaded images.
- Chat history with multiple conversation sessions.
- Vietnamese / English interface switching.
- User authentication, Admin and Customer Service pages.
- Display generated SQL queries for structured-data responses.

## Tech Stack

**Frontend:** React, TypeScript, Vite, Axios, React Router, Recharts  
**Backend:** Python, FastAPI  
**AI / NLP:** Qwen-2.5-0.5B-Instruct, LoRA, RAG  
**Vector Database:** ChromaDB

## Project Structure

- `src/` - React frontend and UI components
- `backend/` - API, chatbot, RAG and data processing modules
- `public/`, `static/` - static assets
