# ArtStyleTransfer Backend Services

This directory contains the cloud-based microservices that power the advanced AI features of the ArtStyleTransfer app. These services are designed to be deployed on [Modal](https://modal.com/).

## 🏗️ Architecture

The backend consists of two main microservices:

### 1. Photo Art Agent (`photo_art_agent`)
**Path:** `backend/photo_art_agent`

This service handles complex image processing and agentic workflows.
- **Entry Point:** `main.py`
- **Key Features:**
  - Semantic Image Editing
  - Background Reconstruction
  - Intelligent Agent Logic (`openrouter_agent.py`)
  - OpenCV based image manipulation (`opencv_tools.py`)

### 2. Match Art Style (`match_art_style`)
**Path:** `backend/match_art_style`

This service is dedicated to the Art Style Transfer feature, utilizing Stable Diffusion XL (SDXL) via Modal's GPU infrastructure.
- **Entry Point:** `main.py`
- **Key Features:**
  - Text-to-Image / Image-to-Image generation
  - Style matching logic
  - Database of art styles (`database_style_transfer`)

## 🚀 Deployment

The services are deployed using the `modal` CLI.

### Prerequisites
- Python 3.10+
- Modal CLI installed (`pip install modal`)
- Modal account and authentication (`modal token new`)

### Deploying Photo Art Agent
```bash
cd photo_art_agent
modal deploy main.py
```

### Deploying Match Art Style
```bash
cd match_art_style
modal deploy main.py
```

## 🔗 Endpoints

The mobile app connects to these services via the URLs defined in `endPoints.js` in the frontend application.
- **Base URL:** Connects to `photo_art_agent`
- **Art Style Base URL:** Connects to `match_art_style`

## 🛠️ Local Development

To run these services locally for development:

```bash
modal serve main.py
```
This will create a temporary development endpoint that hot-reloads on file changes.
