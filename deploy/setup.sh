#!/bin/bash
# Sacred Texts LLM Setup Script
# Hybrid deployment: Local ChromaDB + Cloud OpenRouter LLM

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

# Function to check if OpenRouter API key is valid
check_openrouter_key() {
    local api_key=$1
    if [ -z "$api_key" ] || [ "$api_key" = "your-api-key-here" ]; then
        return 1
    fi
    
    # Test the API key
    local response=$(curl -s -H "Authorization: Bearer $api_key" \
        -H "Content-Type: application/json" \
        "https://openrouter.ai/api/v1/models" 2>/dev/null)
    
    # Check if response contains models (success) or error (failure)
    if echo "$response" | grep -q '"id":' && ! echo "$response" | grep -q '"error"'; then
        return 0
    else
        return 1
    fi
}

print_header() {
    echo ""
    echo "🚀 ========================================="
    echo "   Sacred Texts LLM - Setup"
    echo "   Local ChromaDB + Cloud OpenRouter"
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
        read -p "Do you want to update it with the latest template? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp deploy/env.example .env
            print_success "Updated .env file with latest template"
        fi
    fi
    
    # Ensure OpenRouter is set as provider
    sed -i.bak 's/LLM_PROVIDER=.*/LLM_PROVIDER=openrouter/' .env
    print_success "Configured for OpenRouter provider"
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

setup_openrouter() {
    print_status "Setting up OpenRouter..."
    
    # Load API key from .env
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    # Check if API key is set
    if [ -z "$OPENROUTER_API_KEY" ] || [ "$OPENROUTER_API_KEY" = "your-api-key-here" ]; then
        print_error "OpenRouter API key not configured"
        echo ""
        echo "To get your API key:"
        echo "1. Visit: https://openrouter.ai/keys"
        echo "2. Sign up/login to get your API key"
        echo "3. Edit .env file and set: OPENROUTER_API_KEY=your-key-here"
        echo ""
        read -p "Enter your OpenRouter API key: " api_key
        if [ -n "$api_key" ]; then
            sed -i.bak "s/OPENROUTER_API_KEY=.*/OPENROUTER_API_KEY=$api_key/" .env
            OPENROUTER_API_KEY=$api_key
        else
            print_error "API key is required for OpenRouter"
            exit 1
        fi
    fi
    
    # Test the API key
    print_status "Testing OpenRouter API key..."
    if check_openrouter_key "$OPENROUTER_API_KEY"; then
        print_success "OpenRouter API key is valid"
    else
        print_error "Invalid OpenRouter API key"
        echo "Please check your API key at: https://openrouter.ai/keys"
        exit 1
    fi
    
    # Test model availability
    print_status "Testing model availability..."
    local model="anthropic/claude-3.5-sonnet"
    local response=$(curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY" \
        -H "Content-Type: application/json" \
        "https://openrouter.ai/api/v1/models" 2>/dev/null)
    
    if echo "$response" | grep -q "$model"; then
        print_success "Model $model is available"
    else
        print_warning "Model $model may not be available, but setup will continue"
    fi
}

setup_ollama_fallback() {
    print_status "Setting up Ollama fallback..."
    
    # Check if Ollama is installed
    if ! command_exists ollama; then
        print_warning "Ollama not installed. Installing for fallback..."
        if command_exists brew; then
            brew install ollama
        else
            print_warning "Please install Ollama manually: https://ollama.ai/download"
            print_warning "Fallback to Ollama will not be available"
            return
        fi
    fi
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_success "Ollama is running"
    else
        print_warning "Ollama is not running. Starting for fallback..."
        ollama serve &
        sleep 5
        
        if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            print_warning "Failed to start Ollama. Fallback will not be available."
            return
        fi
    fi
    
    # Check if model is installed
    local model="qwen3:30b-a3b"
    if curl -s http://localhost:11434/api/tags | grep -q "$model"; then
        print_success "Ollama model $model is ready for fallback"
    else
        print_warning "Ollama model $model not found. Installing for fallback..."
        ollama pull "$model"
    fi
}

setup_ngrok() {
    print_status "Setting up ngrok..."
    
    # Check if ngrok is authenticated (multiple possible config locations)
    NGROK_CONFIG_FOUND=false
    
    # Check modern ngrok config location
    if [ -f "$HOME/Library/Application Support/ngrok/ngrok.yml" ]; then
        NGROK_CONFIG_FOUND=true
    # Check legacy location
    elif [ -f ~/.ngrok2/ngrok.yml ]; then
        NGROK_CONFIG_FOUND=true
    fi
    
    if [ "$NGROK_CONFIG_FOUND" = false ]; then
        # Try to authenticate using token from .env if available
        if [ -f .env ]; then
            export $(grep -v '^#' .env | xargs)
            if [ -n "$NGROK_AUTHTOKEN" ] && [ "$NGROK_AUTHTOKEN" != "YOUR_NGROK_TOKEN_HERE" ] && [ "$NGROK_AUTHTOKEN" != "your-ngrok-token-here" ]; then
                print_status "Authenticating ngrok using token from .env..."
                ngrok config add-authtoken "$NGROK_AUTHTOKEN" >/dev/null 2>&1
                if [ $? -eq 0 ]; then
                    print_success "ngrok authenticated successfully"
                    return 0
                fi
            fi
        fi
        
        print_warning "ngrok not authenticated. Please run:"
        print_warning "  ngrok authtoken YOUR_TOKEN"
        print_warning "Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken"
        print_warning "Then run this script again."
        exit 1
    fi
    
    print_success "ngrok is authenticated and ready"
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
    print_status "Testing deployment setup..."
    
    # Test OpenRouter connection
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
        if check_openrouter_key "$OPENROUTER_API_KEY"; then
            print_success "✓ OpenRouter connection test passed"
        else
            print_error "✗ OpenRouter connection test failed"
            return 1
        fi
    fi
    
    # Test Python imports
    if python3 -c "import fastapi, uvicorn, websockets, requests, openai; print('✓ Python dependencies OK')" 2>/dev/null; then
        print_success "✓ Python dependencies test passed"
    else
        print_error "✗ Python dependencies test failed"
        return 1
    fi
    
    # Test web app startup
    print_status "Testing web app startup..."
    python3 deploy/web_app.py &
    WEB_PID=$!
    sleep 5
    
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
    echo "   Setup Complete!"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. 🚀 Deploy your application:"
    echo "   ./deploy/deploy.sh"
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
    echo "5. 💰 Monitor costs:"
    echo "   Check your OpenRouter dashboard: https://openrouter.ai/keys"
    echo ""
    echo "6. 🔄 Switch back to local processing (Ollama):"
    echo "   Edit .env file: LLM_PROVIDER=ollama"
    echo "   ./deploy/deploy.sh restart"
    echo ""
    echo "For help: ./deploy/deploy.sh help"
    echo ""
}

main() {
    print_header
    
    setup_environment
    check_dependencies
    setup_openrouter
    setup_ollama_fallback
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
        setup_openrouter
        setup_ollama_fallback
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
        echo "Sacred Texts LLM - Setup Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  setup, start  - Complete deployment setup (default)"
        echo "  check         - Check if setup is complete"
        echo "  help          - Show this help message"
        echo ""
        echo "This script sets up:"
        echo "  - Environment configuration (.env)"
        echo "  - OpenRouter API key validation"
        echo "  - Ollama fallback setup"
        echo "  - ngrok authentication"
        echo "  - Python dependencies"
        echo "  - Vector store verification"
        echo "  - Web app testing"
        echo ""
        echo "Deployment features:"
        echo "  - Cloud LLM (OpenRouter) for better quality"
        echo "  - Local ChromaDB for data privacy"
        echo "  - Ollama fallback for reliability"
        echo "  - Cost monitoring capabilities"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
