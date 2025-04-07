# GBI Match Maker: Bot & Web Service Setup

This document provides instructions for setting up and running the GBI Match Maker application, which consists of a Telegram bot and a web interface.

## Project Structure

The project can be run in two modes:

1. **Full Stack Mode** - Runs both the Telegram bot and web interface together
2. **Bot-Only Mode** - Runs just the Telegram bot (suitable for deployment)

## Running in Full Stack Mode

To run both the Telegram bot and web interface:

 * Serving Flask app 'app'
 * Debug mode: off

This will:
- Start the Telegram bot in a separate thread
- Run the Flask web application on port 5000
- Set up a self-ping mechanism to prevent idling on free hosting plans

## Running in Bot-Only Mode

To run just the Telegram bot:



This will:
- Start only the Telegram bot
- Set up a minimal health check server on port 5000
- Include the self-ping mechanism to prevent idling

## Environment Variables

The following environment variables are required:

- : Your Telegram bot token from BotFather
- : PostgreSQL database connection string

Optional environment variables:

- : Port for the web server (default: 5000)
- : URL of your deployed application (for self-ping)
- : Service name on Render.com (default: gbi-match-maker)

## Deployment

The project is configured for deployment on Render.com. It includes:

- : Blueprint definition for Render.com
- : Dependencies for deployment
- : Process type definitions for deployment

When deploying, the service will run in Bot-Only Mode by default.

## Database

The application uses PostgreSQL for persistent storage. To update the database schema:

1. Update models in 
2. Run Dropping all tables...
Creating all tables with updated schema...
Database tables recreated successfully! to recreate the database tables

**Warning**: Running  will drop and recreate all tables, resulting in data loss.

## Important Components

- : Bot setup and handlers configuration
- : Telegram command handlers
- : Data management layer
- : Database models
- : Flask web application
- : Entry point for full stack mode
- : Entry point for bot-only mode
