from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from .routes import router

def create_app(dev_mode: bool = False):
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="TAK Manager API",
        description="API for managing TAK Server Docker containers"
    )

    # Add CORS middleware - more permissive in dev mode
    origins = ["http://localhost:3000"] if dev_mode else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router, prefix="/api")

    # Health check endpoint
    @app.get('/health')
    async def health_check():
        return {'status': 'healthy'}

    # Only serve static files in production mode
    if not dev_mode:
        web_dir = Path(__file__).parent.parent / "web" / "dist"
        if web_dir.exists():
            app.mount("/", StaticFiles(directory=str(web_dir), html=True))

    return app 