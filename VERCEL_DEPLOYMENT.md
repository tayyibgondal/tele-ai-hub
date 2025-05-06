# Deploying to Vercel

This document explains how to deploy this Flask application to Vercel.

## Prerequisites

1. A [Vercel](https://vercel.com) account
2. [Vercel CLI](https://vercel.com/docs/cli) installed (optional, for local development)
3. A PostgreSQL database (recommended: [Supabase](https://supabase.com/), [Neon](https://neon.tech/), or [Railway](https://railway.app/))

## Steps for Deployment

1. **Push your code to a GitHub repository**

2. **Connect to Vercel**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "Add New..." > "Project"
   - Select your GitHub repository
   - Configure the project:
     - Framework Preset: Other
     - Root Directory: ./
     - Build Command: Leave default
     - Output Directory: Leave default

3. **Set Environment Variables**
   Go to the project settings > Environment Variables tab and add:
   - `SECRET_KEY`: A secure random string (generate with `openssl rand -base64 32`)
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI features)
   - `FINETUNING_COLAB_SERVER_URL`: URL to your Colab notebook (if using finetuning)

4. **Database Migration**
   - Since Vercel doesn't support running migrations automatically, you'll need to run them locally first:
     ```
     export DATABASE_URL=your_production_database_url
     python -c "from src.app import app, db; app.app_context().push(); db.create_all()"
     ```

5. **Deploy**
   - Vercel will automatically deploy your app when you push to your repository
   - Or manually trigger a new deployment from the Vercel dashboard

## Troubleshooting 404 Errors

If you get a 404 error after deployment, try these steps:

1. **Check Vercel Logs**
   - Go to your Vercel dashboard, select your project, and check "Deployments" 
   - Click on the deployment and select "Functions" to view the logs

2. **Use requirements-minimal.txt**
   - If you're having dependency issues, rename `requirements-minimal.txt` to `requirements.txt` 
   - This contains only the core dependencies needed for the app to run

3. **Verify Environment Variables**
   - Double-check that all required environment variables are correctly set in Vercel

4. **Check API Route Configuration**
   - Make sure your Vercel Functions are properly configured to run on the correct routes

5. **Try Using the Vercel CLI**
   - Deploy with `vercel` command locally to get more detailed error messages:
     ```
     npm install -g vercel
     vercel login
     vercel
     ```

## Limitations on Vercel

1. **Cold Starts**: As a serverless platform, your Flask app might experience cold starts
2. **Ephemeral Filesystem**: Any files written to the filesystem will not persist
3. **Request Timeout**: Vercel has a 10-second execution limit for serverless functions
4. **Heavy Dependencies**: Some of the machine learning libraries might exceed Vercel's function size limit

## Alternatives

If you encounter limitations with Vercel, consider:
- [Railway](https://railway.app/)
- [Render](https://render.com/)
- [DigitalOcean App Platform](https://www.digitalocean.com/products/app-platform/)
- [Heroku](https://www.heroku.com/) 