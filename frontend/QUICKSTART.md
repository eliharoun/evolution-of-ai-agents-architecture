# Quick Start Guide

## ⚠️ Important: ES6 Modules Requirement

This application uses **ES6 modules** which require serving over HTTP protocol. 
**Do NOT open the HTML file directly** - it won't work!

## 🚀 Starting the Application

### Step 1: Start the Backend
```bash
# From project root directory
uvicorn backend.api:app --reload
```
Backend will run at: **http://localhost:8000**

### Step 2: Start the Frontend Server
```bash
# In a new terminal, from project root
cd frontend && python3 -m http.server 8080
```
Frontend will serve at: **http://localhost:8080**

### Step 3: Open in Browser
Navigate to: **http://localhost:8080**

**✅ Correct**: `http://localhost:8080`  
**❌ Wrong**: `file:///path/to/index.html`

## 🔍 Troubleshooting

### "Stages not loading" or "Module errors"
**Problem**: Opened file directly instead of using HTTP server  
**Solution**: Use `http://localhost:8080` in your browser

### "Backend not connected"
**Problem**: Backend not running  
**Solution**: Start backend with `uvicorn backend.api:app --reload`

### "Port already in use"
**Problem**: Port 8080 or 8000 already occupied  
**Solution**: 
- Use different port: `python3 -m http.server 8081`
- Or kill existing process

### "Cannot GET /"
**Problem**: Wrong directory for HTTP server  
**Solution**: Ensure you're in `frontend/` directory when starting server

## ✅ Verification

When correctly set up, you should see:
1. Stage dropdown populates with available stages
2. Context monitor shows Stage 1
3. Chat interface is ready
4. No console errors in browser DevTools

## 🎯 Alternative: Using npm/node

If you prefer Node.js:
```bash
# Install http-server globally (one time)
npm install -g http-server

# Start frontend server
cd frontend && http-server -p 8080
```

Then navigate to `http://localhost:8080`
