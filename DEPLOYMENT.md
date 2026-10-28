# Deployment Guide: AP-QAIC Prototype (QEXPO 2026 UC 090)

The project is packaged for both local production serving and one-click cloud deployment.

---

## 1. Local Production Deployment (Active Now)
The application is currently running live on:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

To manually restart or run in production mode on Windows:
```powershell
python hack.py
```

---

## 2. Cloud 1-Click Deployment Options

### Option A: Render (Free Tier)
1. Push your repository to GitHub:
   ```bash
   git remote add origin https://github.com/<YOUR-USERNAME>/ap-qaic-pipeline.git
   git branch -M main
   git push -u origin main
   ```
2. Go to [dashboard.render.com](https://dashboard.render.com)
3. Click **New +** -> **Web Service** -> Connect your GitHub repository.
4. Render automatically reads [`render.yaml`](file:///c:/Users/srinu/ajay/render.yaml) and [`requirements.txt`](file:///c:/Users/srinu/ajay/requirements.txt).
5. Click **Deploy Web Service** to get a live URL: `https://ap-qaic-quantum-pipeline.onrender.com`.

---

### Option B: Railway (Free / Instant)
1. Go to [railway.app](https://railway.app)
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Railway automatically detects the [`Dockerfile`](file:///c:/Users/srinu/ajay/Dockerfile) and assigns a public `*.up.railway.app` domain.

---

### Option C: Vercel
1. Install or run Vercel CLI:
   ```bash
   npx vercel
   ```
   Or connect your GitHub repo on [vercel.com](https://vercel.com).
2. It automatically deploys using [`vercel.json`](file:///c:/Users/srinu/ajay/vercel.json).

---

### Option D: Containerized Docker Deployment
To build and run anywhere with Docker:
```bash
docker build -t ap-qaic-quantum:latest .
docker run -d -p 5000:5000 --name ap-qaic-app ap-qaic-quantum:latest
```
Access via `http://localhost:5000`.
