web: gunicorn -k uvicorn.workers.UvicornWorker --workers 1 app.main:app
worker: python -m app.telegram.bot
