import os
import uvicorn

if __name__ == "__main__":
    is_dev = os.getenv("ENV", "development") == "development"

    uvicorn.run(
        "app.main:app",  # ← this is the import string
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=is_dev,
        ssl_keyfile=os.getenv("SSL_KEY_PATH") if is_dev else None,
        ssl_certfile=os.getenv("SSL_CERT_PATH") if is_dev else None,
    )