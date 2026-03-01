# 🚀 OpenAgent Deployment Guide

Follow these steps to deploy OpenAgent to the cloud for free.

## Option 1: Hugging Face Spaces (Recommended)

This is the best option for AI projects as it provides 16GB RAM for free.

### Step 1: Create a New Space
1. Go to [huggingface.co/spaces](https://huggingface.co/new-space) (Log in or Sign up).
2. **Space Name**: `open-agent` (or anything you like).
3. **SDK**: Choose **Docker**.
4. **Template**: Choose **Blank**.
5. **Space Hardware**: Keep the default "CPU basic • 2 vCPU • 16 GB • Free".
6. Click **Create Space**.

### Step 2: Add Your Groq API Key
1. In your new Space, go to the **Settings** tab.
2. Scroll down to **Variables and secrets**.
3. Click **New secret**.
4. **Name**: `GROQ_API_KEY`
5. **Value**: Paste your Groq API key (starts with `gsk_...`).
6. Click **Save**.

### Step 3: Upload the Code
1. In your Space, click the **Files** tab.
2. Click **Add file** -> **Upload files**.
3. Drag and drop all the files from your local `openagent` folder.
4. **Wait** for the build to finish (it will take 2-3 minutes to install dependencies).
5. Once complete, your agent will be live at a public URL!

---

## Option 2: Render.com

1. Create a new **Web Service** on [Render](https://dashboard.render.com).
2. Connect your GitHub repository.
3. **Environment**: `Docker`.
4. **Advanced Settings**: Add an Environment Variable `GROQ_API_KEY`.
5. Click **Deploy**.

---

## Final Health Check
Once deployed, verify:
- [ ] UI loads correctly.
- [ ] Groq status shows "Online".
- [ ] File uploads work.

**Happy Deploying! 🚀**
