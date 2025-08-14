#!/bin/bash
"""
Phase 1 Setup Script for Sacred Texts LLM
Sets up local Ollama deployment with ngrok exposure
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Ollama is running
check_ollama() {
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check if model is installed
check_model() {
    local model=$1
    if curl -s http://localhost:11434/api/tags | grep -q "$model"; then
        return 0
    else
        return 1
    fi
}

print_header() {
    echo ""
    echo "🚀 ========================================="
    echo "   Sacred Texts LLM - Phase 1 Setup"
    echo "   Local Ollama + ngrok exposure"
    echo "========================================="
    echo ""
}

setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        if [ -f deploy/env.example ]; then
            cp deploy/env.example .env
            print_success "Created .env file from template"
        else
            print_error "deploy/env.example not found. Please create .env file manually."
            exit 1
        fi
    else
        print_warning ".env file already exists"
    fi
    
    # Ensure Phase 1 settings
    sed -i.bak 's/LLM_PROVIDER=.*/LLM_PROVIDER=ollama/' .env
    print_success "Configured for Phase 1 (Ollama)"
}

check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if ! command_exists pip3; then
        print_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check Ollama
    if ! command_exists ollama; then
        print_error "Ollama is required but not installed"
        print_error "Install from: https://ollama.ai/download"
        exit 1
    fi
    
    # Check ngrok
    if ! command_exists ngrok; then
        print_warning "ngrok not found. Installing..."
        if command_exists brew; then
            brew install ngrok/ngrok/ngrok
        else
            print_error "Please install ngrok manually: https://ngrok.com/download"
            exit 1
        fi
    fi
    
    print_success "Dependencies check complete"
}

setup_ollama() {
    print_status "Setting up Ollama..."
    
    # Check if Ollama is running
    if ! check_ollama; then
        print_warning "Ollama is not running. Starting Ollama..."
        ollama serve &
        sleep 5
        
        if ! check_ollama; then
            print_error "Failed to start Ollama. Please start it manually: ollama serve"
            exit 1
        fi
    fi
    
    print_success "Ollama is running"
    
    # Check if model is installed
    MODEL_NAME="qwen3:30b-a3b"
    if ! check_model "$MODEL_NAME"; then
        print_warning "Model $MODEL_NAME not found. Installing..."
        print_warning "This may take 10-30 minutes depending on your internet connection..."
        ollama pull "$MODEL_NAME"
        
        if ! check_model "$MODEL_NAME"; then
            print_error "Failed to install model $MODEL_NAME"
            exit 1
        fi
    fi
    
    print_success "Ollama model $MODEL_NAME is ready"
}

setup_ngrok() {
    print_status "Setting up ngrok..."
    
    # Check if ngrok is authenticated
    if [ ! -f ~/.ngrok2/ngrok.yml ]; then
        print_warning "ngrok not authenticated. Please run:"
        print_warning "  ngrok authtoken YOUR_TOKEN"
        print_warning "Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken"
        print_warning "Then run this script again."
        exit 1
    fi
    
    print_success "ngrok is configured"
}

install_python_deps() {
    print_status "Installing Python dependencies..."
    pip3 install -r requirements.txt
    print_success "Python dependencies installed"
}

check_vector_store() {
    print_status "Checking vector store..."
    
    if [ ! -d "vector_store" ]; then
        print_error "Vector store not found. Please run ingestion first:"
        print_error "  python data/ingest.py"
        print_error "This will download and process the sacred texts."
        exit 1
    fi
    
    print_success "Vector store found"
}

test_setup() {
    print_status "Testing setup..."
    
    # Test Ollama
    if check_ollama; then
        print_success "✓ Ollama connection test passed"
    else
        print_error "✗ Ollama connection test failed"
        return 1
    fi
    
    # Test Python imports
    if python3 -c "import fastapi, uvicorn, websockets, requests; print('✓ Python dependencies OK')" 2>/dev/null; then
        print_success "✓ Python dependencies test passed"
    else
        print_error "✗ Python dependencies test failed"
        return 1
    fi
    
    # Test web app startup
    print_status "Testing web app startup..."
    timeout 10s python3 deploy/web_app.py &
    WEB_PID=$!
    sleep 3
    
    if curl -s http://localhost:8001/health >/dev/null 2>&1; then
        print_success "✓ Web app test passed"
        kill $WEB_PID 2>/dev/null || true
    else
        print_error "✗ Web app test failed"
        kill $WEB_PID 2>/dev/null || true
        return 1
    fi
    
    return 0
}

show_next_steps() {
    echo ""
    echo "🎉 ========================================="
    echo "   Phase 1 Setup Complete!"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. 🚀 Deploy your application:"
    echo "   ./deploy.sh"
    echo ""
    echo "2. 🌐 Access your application:"
    echo "   Local: http://localhost:8001"
    echo "   Public: URL will be shown by ngrok"
    echo ""
    echo "3. 🧪 Test the setup:"
    echo "   python deploy/test_web.py"
    echo ""
    echo "4. 📚 Use the CLI (unchanged):"
    echo "   python chat.py          # Simple chat"
    echo "   python agent_chat.py    # Deep research"
    echo ""
    echo "5. 🔄 Switch to OpenRouter (Phase 2):"
    echo "   ./deploy/setup_phase2.sh"
    echo ""
    echo "For help: ./deploy/deploy.sh help"
    echo ""
}

main() {
    print_header
    
    setup_environment
    check_dependencies
    setup_ollama
    setup_ngrok
    install_python_deps
    check_vector_store
    
    if test_setup; then
        show_next_steps
    else
        print_error "Setup test failed. Please check the errors above."
        exit 1
    fi
}

# Parse command line arguments
case "${1:-setup}" in
    "setup"|"start")
        main
        ;;
    "check")
        print_header
        check_dependencies
        setup_ollama
        setup_ngrok
        check_vector_store
        if test_setup; then
            print_success "All checks passed!"
        else
            print_error "Some checks failed."
            exit 1
        fi
        ;;
    "help"|"-h"|"--help")
        echo "Sacred Texts LLM - Phase 1 Setup Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  setup, start  - Complete Phase 1 setup (default)"
        echo "  check         - Check if setup is complete"
        echo "  help          - Show this help message"
        echo ""
        echo "This script sets up:"
        echo "  - Environment configuration (.env)"
        echo "  - Ollama with qwen3:30b-a3b model"
        echo "  - ngrok authentication"
        echo "  - Python dependencies"
        echo "  - Vector store verification"
        echo "  - Web app testing"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
