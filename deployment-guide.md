# GBI Match Maker Deployment Guide

This guide will walk you through deploying the GBI Match Maker Telegram bot on Render.com.

## Prerequisites

1. A Render.com account (free tier is sufficient)
2. A Telegram bot token (obtained from BotFather)

## Deployment Steps

### 1. Fork or Clone the Repository

First, ensure you have a copy of the codebase either by forking this repository or cloning it to your own GitHub account.

### 2. Connect to Render

1. Log in to your Render.com account
2. Click "New" and select "Blueprint" from the dropdown menu
3. Connect your GitHub account if you haven't already
4. Select the repository containing the GBI Match Maker code
5. Click "Connect"

### 3. Configure the Blueprint

Render will automatically detect the `render.yaml` file in the repository, which contains the configuration for:
- A web service (the Telegram bot)
- A PostgreSQL database

You'll need to:
1. Review the suggested resources
2. Provide your TELEGRAM_BOT_TOKEN (you'll be prompted for this)
3. Click "Apply" to create the resources

### 4. Wait for Deployment

Render will now:
1. Create a PostgreSQL database
2. Build and deploy the web service that runs the Telegram bot
3. Connect the two resources

This process typically takes 5-10 minutes.

### 5. Verify Deployment

Once deployment is complete:
1. Open the web service in Render
2. Check the logs to ensure the bot started successfully
3. Try interacting with your bot on Telegram to confirm it's working

## Environment Variables

The following environment variables are configured automatically:
- `DATABASE_URL`: Connection string for the PostgreSQL database (set automatically)
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (you must provide this)
- `PORT`: The port for the health check server (set to 5000)
- `APP_URL`: The URL of your deployed application (needed for self-ping)

## Important Features

### Health Check Server

The bot runs a simple health check server on port 5000 that responds to HTTP requests. Render uses this to monitor the application's health.

### Self-Ping Mechanism

To prevent the bot from being idled on Render's free tier, the application includes a self-ping mechanism that sends an HTTP request to itself every 13 minutes.

## Troubleshooting

If your bot isn't responding:

1. Check the Render logs for any error messages
2. Verify your Telegram bot token is correct
3. Make sure the bot is properly activated in Telegram (send /start to your bot)
4. Check the database connection is working properly

## Database Migration

If you need to update the database schema:

1. Make your changes to the models in `models.py`
2. Access the Render shell for your service
3. Run the following command:
```
python recreate_tables.py
```

WARNING: This will recreate all tables, resulting in data loss. Only use this during initial setup or if you're okay with losing existing data.

## Need Help?

If you encounter any issues, check the logs in the Render dashboard or reach out to the developer for assistance.
