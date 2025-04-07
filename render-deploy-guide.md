# Deployment Guide for GBI Match Maker on Render

This guide will walk you through deploying the GBI Match Maker application on Render using a single web service that runs both the Flask web app and Telegram bot.

## Prerequisites

1. A GitHub account with your project repository
2. A Render account (https://render.com)
3. A Telegram bot token (from BotFather)

## Step 1: Create a PostgreSQL Database on Render

1. Log in to your Render dashboard
2. Go to "New" > "PostgreSQL"
3. Configure your database:
   - Name: `gbi-match-maker-db`
   - Database: `gbi_match_maker`
   - User: Let Render generate it
   - Version: PostgreSQL 15
   - Plan: Free
4. Click "Create Database"
5. Note the Internal Database URL

## Step 2: Deploy the Web Service (Combined Web + Bot)

1. From your Render dashboard, go to "New" > "Web Service"
2. Connect your GitHub repository
3. Configure the web service:
   - Name: `gbi-match-maker`
   - Runtime: Python 3
   - Build Command: `pip install -r requirements-render.txt`
   - Start Command: `gunicorn wsgi:application --bind 0.0.0.0:$PORT`
   - Plan: Free
4. Add environment variables:
   - `DATABASE_URL`: Use the Internal Database URL from step 1
   - `SESSION_SECRET`: Generate a random string
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
5. Click "Create Web Service"

## Step 3: Verify Deployment

1. Wait for the service to deploy successfully (this may take a few minutes)
2. Access your web application at the provided URL from Render
3. Test your Telegram bot by messaging it on Telegram

## How It Works

This deployment approach:
1. Runs both the web application and Telegram bot in a single web service
2. Uses a multi-threaded approach to handle both simultaneously
3. Eliminates the need for a separate background worker (which requires a paid plan)

## Troubleshooting

If you encounter issues with the deployment:

1. Check the logs in the Render dashboard
2. Verify that all environment variables are correctly set
3. Ensure your Telegram bot token is valid
4. Check that your PostgreSQL database is properly initialized

## Notes on Free Tier Limitations

- The free tier on Render has some limitations:
  - Services will spin down after periods of inactivity
  - The PostgreSQL free tier is limited to 1GB storage
  - There are monthly compute hours limits
- For better reliability and performance, consider upgrading to a paid plan
