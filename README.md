# AI Dev Workspace

Local AI development environment using **Docker** and **Ollama** to run coding models like **DeepSeek-Coder** locally.

This setup allows you to run an AI coding assistant completely offline and connect it to your code editor.

---

# Project Structure

```
ai-dev-workspace/
│
├── docker/
│   └── docker-compose.yml
│
├── app/
│   └── test.py
│
├── prompts/
│   └── examples.md
│
└── README.md
```

---

# Requirements

* Docker installed
* Docker Compose
* 16 GB RAM recommended
* Internet connection (only needed for first model download)

---

# Start AI Server

Navigate to docker folder:

```sh
cd docker
```

Start container:

```sh
docker compose up -d
```

---

# Check Running Containers

```sh
docker ps
```

---

# List Docker Images

```sh
docker images
```

---

# Check Installed Models

```sh
docker exec -it ollama ollama list
```

---

# Download Coding Model

```sh
docker exec -it ollama ollama pull deepseek-coder:1.3b
docker exec -it ollama ollama pull codellama:7b-code-q4_1
docker exec -it ollama ollama pull santacoder:1.1b
```
This downloads the **DeepSeek coding model (~3.8GB)**.

---

# Verify Model Installation

```sh
docker exec -it ollama ollama list
```

Expected output:

```
NAME                 SIZE
deepseek-coder:6.7b  ~3.8GB
```

---

# Run the Model

```sh
docker exec -it ollama ollama run deepseek-coder
```

Example prompt:

```
Write a Python quicksort function
```

Exit the model:

```
/bye
```

---

# Test Ollama API

Local AI server runs at:

```
http://localhost:11434
```

Example API request:

```sh
curl http://localhost:11434/api/generate \
-d '{
"model":"deepseek-coder:6.7b",
"prompt":"write a python fibonacci function"
}'
```

---

# Stop the Server

```sh
docker compose down
```

---

# Useful Docker Commands

Start container

```sh
docker compose up -d
```

Stop container

```sh
docker compose down
```

Check containers

```sh
docker ps
```

Check images

```sh
docker images
```

---

# PowerShell Command History

Show command history:

```sh
Get-History
```

Run a previous command:

```sh
Invoke-History <id>
```

Example:

```sh
Invoke-History 2
```

---

# Installed Commands History (Example)

Example commands used during setup:

```sh
docker compose up -d
docker manifest inspect ollama/ollama:0.3.12
docker images
docker exec -it ollama ollama list
docker exec -it ollama ollama pull deepseek-coder:6.7b
docker exec -it ollama ollama run deepseek-coder


docker exec -it ollama ollama rm codellama:7b-code-q4_1
```

---

# Future Improvements

Possible extensions for this project:

* Add web interface for AI chat
* Add multiple AI models
* Connect to code editor AI extension
* Add document search (RAG)
* Enable GPU acceleration

---

# Notes

* Models are stored in Docker volume.
* First download may take several minutes.
* Requires several GB of disk space.
* Works completely offline after models are downloaded.

---
