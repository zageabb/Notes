import os

from notes_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.getenv("NOTES_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", os.getenv("NOTES_PORT", "5063"))),
        debug=os.getenv("NOTES_DEBUG", "0") == "1",
    )
