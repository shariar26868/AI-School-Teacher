# How to Get Your Gemini API Key

## ⚠️ Important: You're Using the Wrong API Key!

Your current key (`AIza...`) is a **Google Cloud API Key**, but Gemini needs a **Generative AI API Key**.

They are DIFFERENT and NOT interchangeable!

---

## ✅ Correct Way to Get Gemini API Key

### Step 1: Go to Google AI Studio
**URL:** https://aistudio.google.com/app/apikey

### Step 2: Click "Get API Key" (Top Right)

### Step 3: Select your project or create a new one
- Click "Create API Key"
- Select a project (or create new)
- Click "Create API Key in new project"

### Step 4: Copy Your API Key
- A new API key will appear
- It will look like: `AIzaSyD...xxxxx...` (longer format)
- **COPY THIS KEY**

### Step 5: Update Your .env File

Open `.env` and replace:
```env
# OLD (WRONG - Google Cloud key):
GEMINI_API_KEY=AIzaSyCjhnFDkNLJK5JspaXxk9lX6QGkG9bMd9o

# NEW (CORRECT - Generative AI key):
GEMINI_API_KEY=AIzaSyD_YOUR_ACTUAL_GEMINI_KEY_HERE
```

### Step 6: Restart Server

The server will reload automatically. Test the mindmap again!

---

## 🔍 How to Verify You Have the Right Key

1. The key should be generated from **aistudio.google.com/app/apikey**
2. NOT from **console.cloud.google.com**
3. Check if it says "Generative AI API" in the Google AI Studio dashboard

---

## 📝 What to Do Now

1. Go to: https://aistudio.google.com/app/apikey
2. Create/Get your Generative AI API key
3. Replace the value in `.env` file for `GEMINI_API_KEY`
4. Save the file
5. Server will auto-reload
6. Test mindmap generation again

Still having issues? The error will be clearer once you have the correct key! 🚀
