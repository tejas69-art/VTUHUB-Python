# Docker Setup for Windows

## Install Docker Desktop

1. **Download Docker Desktop for Windows:**
   - Go to: https://www.docker.com/products/docker-desktop/
   - Download "Docker Desktop for Windows"
   - Run the installer

2. **After Installation:**
   - Restart your computer if prompted
   - Launch Docker Desktop
   - Wait for Docker to start (whale icon in system tray)

3. **Verify Installation:**
   ```powershell
   docker --version
   docker ps
   ```

## Test Your Build

Once Docker is installed, run:

```powershell
cd C:\Users\tejas\rre\VTUHUB-Python
docker build -f Dockerfile.cpu -t vtuhub-test .
```

## Run the Container

After successful build:

```powershell
docker run -p 8000:8000 vtuhub-test
```

Then visit: http://localhost:8000

## Alternative: Test Without Docker

If you don't want to install Docker, you can:
1. Deploy directly to Render/Railway (they'll build it for you)
2. Test locally with Python directly (without Docker)

