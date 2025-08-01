import os
import uvicorn
from app.main import app  # Your FastAPI app

def run():
    is_dev = os.getenv("ENV", "development") == "development"

    ssl_keyfile = os.getenv("SSL_KEY_PATH", "music-button.test-key.pem")
    ssl_certfile = os.getenv("SSL_CERT_PATH", "music-button.test.pem")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=is_dev,
        ssl_keyfile=ssl_keyfile if is_dev else None,
        ssl_certfile=ssl_certfile if is_dev else None,
    )

if __name__ == "__main__":
    run()