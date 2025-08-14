#!/bin/bash
"""
Continuous Deployment Script for Sacred Texts LLM
Handles local development, ngrok exposure, and deployment updates
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WEB_PORT=${WEB_PORT:-8001}
WEB_HOST=${WEB_HOST:-0.0.0.0}
NGROK_REGION=${NGROK_REGION:-us}

# Function to print colored output
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

# Function to check if port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to kill process on port
kill_port() {
    if port_in_use $1; then
        print_warning "Port $1 is in use. Killing existing process..."
        lsof -ti :$1 | xargs kill -9
        sleep 2
    fi
}

# Function to check dependencies
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

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    pip3 install -r requirements.txt
    print_success "Dependencies installed"
}

# Function to check vector store
check_vector_store() {
    print_status "Checking vector store..."
    
    if [ ! -d "vector_store" ]; then
        print_error "Vector store not found. Please run ingestion first:"
        print_error "  python data/ingest.py"
        exit 1
    fi
    
    print_success "Vector store found"
}

# Function to start web server
start_web_server() {
    print_status "Starting web server on port $WEB_PORT..."
    
    # Kill any existing process on the port
    kill_port $WEB_PORT
    
    # Start the web server in background
    python3 deploy/web_app.py &
    WEB_PID=$!
    
    # Wait a moment for server to start
    sleep 3
    
    # Check if server started successfully
    if ! port_in_use $WEB_PORT; then
        print_error "Failed to start web server"
        exit 1
    fi
    
    print_success "Web server started (PID: $WEB_PID)"
    echo $WEB_PID > .web_server.pid
}

# Function to start ngrok tunnel
start_ngrok() {
    print_status "Starting ngrok tunnel..."
    
    # Check if ngrok is authenticated
    if [ ! -f ~/.ngrok2/ngrok.yml ]; then
        print_warning "ngrok not authenticated. Please run:"
        print_warning "  ngrok authtoken YOUR_TOKEN"
        print_warning "Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken"
        exit 1
    fi
    
    # Start ngrok tunnel
    ngrok http $WEB_PORT --region $NGROK_REGION > .ngrok.log 2>&1 &
    NGROK_PID=$!
    
    # Wait for ngrok to start
    sleep 5
    
    # Get the public URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$NGROK_URL" ]; then
        print_error "Failed to get ngrok URL"
        exit 1
    fi
    
    print_success "ngrok tunnel started: $NGROK_URL"
    echo $NGROK_PID > .ngrok.pid
    echo $NGROK_URL > .ngrok_url
    
    # Display the URL prominently
    echo ""
    echo "🚀 ========================================="
    echo "   Sacred Texts LLM is now live!"
    echo "   URL: $NGROK_URL"
    echo "   Local: http://localhost:$WEB_PORT"
    echo "========================================="
    echo ""
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    
    # Stop web server
    if [ -f .web_server.pid ]; then
        WEB_PID=$(cat .web_server.pid)
        if kill -0 $WEB_PID 2>/dev/null; then
            kill $WEB_PID
            print_success "Web server stopped"
        fi
        rm -f .web_server.pid
    fi
    
    # Stop ngrok
    if [ -f .ngrok.pid ]; then
        NGROK_PID=$(cat .ngrok.pid)
        if kill -0 $NGROK_PID 2>/dev/null; then
            kill $NGROK_PID
            print_success "ngrok tunnel stopped"
        fi
        rm -f .ngrok.pid
    fi
    
    rm -f .ngrok_url
}

# Function to show status
show_status() {
    print_status "Current deployment status:"
    
    if [ -f .web_server.pid ]; then
        WEB_PID=$(cat .web_server.pid)
        if kill -0 $WEB_PID 2>/dev/null; then
            print_success "Web server running (PID: $WEB_PID)"
        else
            print_warning "Web server PID file exists but process not running"
        fi
    else
        print_warning "Web server not running"
    fi
    
    if [ -f .ngrok.pid ]; then
        NGROK_PID=$(cat .ngrok.pid)
        if kill -0 $NGROK_PID 2>/dev/null; then
            print_success "ngrok tunnel running (PID: $NGROK_PID)"
            if [ -f .ngrok_url ]; then
                NGROK_URL=$(cat .ngrok_url)
                print_success "Public URL: $NGROK_URL"
            fi
        else
            print_warning "ngrok PID file exists but process not running"
        fi
    else
        print_warning "ngrok tunnel not running"
    fi
}

# Function to restart services
restart_services() {
    print_status "Restarting services..."
    stop_services
    sleep 2
    start_web_server
    start_ngrok
}

# Function to show logs
show_logs() {
    print_status "Recent logs:"
    
    if [ -f .ngrok.log ]; then
        echo "=== ngrok logs ==="
        tail -20 .ngrok.log
        echo ""
    fi
    
    if [ -f .web_server.log ]; then
        echo "=== web server logs ==="
        tail -20 .web_server.log
    fi
}

# Function to clean up
cleanup() {
    print_status "Cleaning up..."
    stop_services
    rm -f .web_server.pid .ngrok.pid .ngrok_url .ngrok.log .web_server.log
    print_success "Cleanup complete"
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Main deployment function
deploy() {
    print_status "Starting Sacred Texts LLM deployment..."
    
    check_dependencies
    install_dependencies
    check_vector_store
    start_web_server
    start_ngrok
    
    print_success "Deployment complete!"
    print_status "Press Ctrl+C to stop all services"
    
    # Keep the script running
    while true; do
        sleep 10
        # Check if services are still running
        if [ -f .web_server.pid ]; then
            WEB_PID=$(cat .web_server.pid)
            if ! kill -0 $WEB_PID 2>/dev/null; then
                print_error "Web server died unexpectedly"
                break
            fi
        fi
        
        if [ -f .ngrok.pid ]; then
            NGROK_PID=$(cat .ngrok.pid)
            if ! kill -0 $NGROK_PID 2>/dev/null; then
                print_error "ngrok tunnel died unexpectedly"
                break
            fi
        fi
    done
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy"|"start")
        deploy
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        echo "Sacred Texts LLM Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy, start  - Start web server and ngrok tunnel (default)"
        echo "  stop          - Stop all services"
        echo "  restart       - Restart all services"
        echo "  status        - Show current deployment status"
        echo "  logs          - Show recent logs"
        echo "  cleanup       - Stop services and clean up files"
        echo "  help          - Show this help message"
        echo ""
        echo "Environment variables:"
        echo "  WEB_PORT      - Web server port (default: 8001)"
        echo "  WEB_HOST      - Web server host (default: 0.0.0.0)"
        echo "  NGROK_REGION  - ngrok region (default: us)"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
