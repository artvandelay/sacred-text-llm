#!/usr/bin/env python3
"""
Check ingestion progress and system status
"""

import os
import subprocess
import chromadb
from config import VECTOR_STORE_DIR, COLLECTION_NAME

def check_ingestion_process():
    """Check if ingestion is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'python.*ingest.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pid = result.stdout.strip()
            return f"✅ Ingestion running (PID: {pid})"
        else:
            return "❌ Ingestion not running"
    except Exception as e:
        return f"❓ Could not check process: {e}"

def check_vector_store():
    """Check vector store status"""
    try:
        if not os.path.exists(VECTOR_STORE_DIR):
            return "❌ Vector store directory not found"
        
        client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        count = collection.count()
        
        if count == 0:
            return "⏳ Vector store empty (ingestion starting)"
        elif count < 1000:
            return f"🚧 Vector store building ({count:,} documents)"
        else:
            return f"✅ Vector store ready ({count:,} documents)"
            
    except Exception as e:
        return f"❌ Vector store error: {e}"

def check_log_file():
    """Check recent log entries"""
    log_file = "logs/ingest.log"
    if not os.path.exists(log_file):
        return "❌ Log file not found"
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            return "❌ Log file empty"
        
        # Get last few lines
        recent = ''.join(lines[-3:]).strip()
        return f"📝 Recent log:\n{recent}"
        
    except Exception as e:
        return f"❌ Could not read log: {e}"

def main():
    print("Sacred Texts LLM - Status Check")
    print("=" * 40)
    
    print(f"Process Status: {check_ingestion_process()}")
    print(f"Vector Store: {check_vector_store()}")
    print(f"Log Status: {check_log_file()}")
    
    print("\n" + "=" * 40)
    print("Commands:")
    print("• Monitor progress: tail -f logs/ingest.log")
    print("• Test chat: python chat.py")
    print("• Simple query: python query.py 'your question'")

if __name__ == "__main__":
    main()
