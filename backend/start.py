#!/usr/bin/env python3
"""
Startup script for the AI Website Navigator Backend
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def check_environment():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("⚠️  .env file not found. Creating from template...")
        if os.path.exists('env.example'):
            if platform.system() == "Windows":
                subprocess.run(['copy', 'env.example', '.env'], shell=True)
            else:
                subprocess.run(['cp', 'env.example', '.env'])
            print("📝 Created .env file. Please edit it with your configuration.")
            return False
        else:
            print("❌ env.example file not found")
            return False
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_openai_key():
    """Check if OpenAI API key is configured"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_openai_api_key_here':
        print("⚠️  OpenAI API key not configured in .env file")
        print("   Please add your OpenAI API key to continue")
        return False
    
    print("✅ OpenAI API key configured")
    return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting AI Website Navigator Backend...")
    
    try:
        import uvicorn
        from config import settings
        
        uvicorn.run(
            "main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.environment == "development",
            log_level=settings.log_level.lower()
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("🤖 AI Website Navigator Backend Startup")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print("❌ main.py not found. Make sure you're in the backend directory")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print("\n📝 Please configure your .env file and run this script again")
        sys.exit(1)
    
    # Check OpenAI key
    if not check_openai_key():
        print("\n🔑 Please add your OpenAI API key to .env file:")
        print("   OPENAI_API_KEY=your_actual_api_key_here")
        sys.exit(1)
    
    print("\n🎯 All checks passed!")
    print("📊 API Documentation will be available at: http://localhost:8000/docs")
    print("🔍 API Health check: http://localhost:8000/health")
    print("\n" + "=" * 40)
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()
