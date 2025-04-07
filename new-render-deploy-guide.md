# Telegram Bot Deployment Guide for GBI Match Maker

This guide explains how to deploy the GBI Match Maker Telegram bot on Render.com.

## Prerequisites

1. A Render.com account
2. A PostgreSQL database (you can use Render's managed PostgreSQL service)
3. A Telegram Bot Token (from @BotFather on Telegram)

## Deployment Steps

### Step 1: Set Up PostgreSQL Database

1. Log in to your Render dashboard
2. Go to "PostgreSQL" in the left sidebar
3. Click "New PostgreSQL"
4. Fill in the details:
   - Name: `gbi-match-maker-db` (or any name you prefer)
   - Database: `gbi_match_maker`
   - User: Leave as default
   - Region: Choose the closest to your target users
5. Click "Create Database"
6. After creation, note the "Internal Database URL" - you'll need this later

### Step 2: Deploy the Web Service

1. In your Render dashboard, go to "Web Services" in the left sidebar
2. Click "New Web Service"
3. Connect your GitHub repository (or use the manual deploy option)
4. Fill in the details:
   - Name: `gbi-match-maker`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements-render.txt`
   - Start Command: `python bot_only.py`
   - Select the appropriate plan (even the free plan works)

5. Add the following environment variables:
   - `DATABASE_URL`: The Internal Database URL from Step 1
   - `TELEGRAM_BOT_TOKEN`: Your Telegram Bot token
   - `PORT`: 5000 (or any port you prefer)

6. Click "Create Web Service"

## Verifying the Deployment

After deployment, there are two ways to check if your service is running:

1. **Web Health Check**: Visit the deployed URL in your browser. You should see a message "GBI Match Maker Bot is running!"
2. **Telegram Test**: Open your Telegram bot and send the `/start` command to verify the bot is functioning correctly.

## Troubleshooting

If you encounter any issues:

1. **Bot not responding**: Check that your `TELEGRAM_BOT_TOKEN` is correct and that the bot is properly initialized in the application
2. **Database connection issues**: Verify your `DATABASE_URL` is correct and that the database is accessible
3. **Application crashes**: Check the Render logs for any error messages

## Updating Your Deployment

To update your application after making changes:

1. Push your changes to your GitHub repository
2. Render will automatically detect the changes and redeploy the application
3. Monitor the deployment logs to ensure everything is working correctly