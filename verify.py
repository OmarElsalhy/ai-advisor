#!/usr/bin/env python3
"""Verification script for ShopSpace AI Business Advisor setup."""

import sys
from pathlib import Path

def check_structure():
    """Verify project structure."""
    print("🔍 Checking project structure...")
    
    required_files = [
        "app/main.py",
        "app/config.py",
        "app/database.py",
        "app/rag.py",
        "app/llm.py",
        "app/ingest.py",
        "requirements.txt",
        ".env.example",
        "Dockerfile",
        "DEPLOYMENT.md",
        "README.md",
    ]
    
    ai_advisor_dir = Path(__file__).parent
    missing = []
    
    for file in required_files:
        path = ai_advisor_dir / file
        if not path.exists():
            missing.append(file)
            print(f"  ❌ Missing: {file}")
        else:
            print(f"  ✅ Found: {file}")
    
    return len(missing) == 0

def check_imports():
    """Verify Python imports work."""
    print("\n🔍 Checking Python imports...")
    
    try:
        from app.config import (
            STORAGE_DIR, CHROMA_DIR, DATABASE_PATH,
            KNOWLEDGE_ROOT, GENERAL_GUIDES_DIR, BUSINESS_GUIDES_DIR
        )
        print("  ✅ Config imports OK")
    except Exception as e:
        print(f"  ❌ Config import failed: {e}")
        return False
    
    try:
        from app.database import initialize, connection
        print("  ✅ Database imports OK")
    except Exception as e:
        print(f"  ❌ Database import failed: {e}")
        return False
    
    try:
        from app.ingest import ingest, COLLECTION_NAME, EMBEDDING_MODEL
        print("  ✅ Ingest imports OK")
    except Exception as e:
        print(f"  ❌ Ingest import failed: {e}")
        return False
    
    try:
        from app.rag import retriever
        print("  ✅ RAG imports OK")
    except Exception as e:
        print(f"  ❌ RAG import failed: {e}")
        return False
    
    try:
        from app.llm import answer
        print("  ✅ LLM imports OK")
    except Exception as e:
        print(f"  ❌ LLM import failed: {e}")
        return False
    
    return True

def check_knowledge_base():
    """Verify knowledge base directories exist."""
    print("\n🔍 Checking knowledge base...")
    
    try:
        from app.config import GENERAL_GUIDES_DIR, BUSINESS_GUIDES_DIR
        
        general_exists = GENERAL_GUIDES_DIR.exists()
        business_exists = BUSINESS_GUIDES_DIR.exists()
        
        if general_exists:
            guides = list(GENERAL_GUIDES_DIR.glob("*.md"))
            print(f"  ✅ general_guides/: {len(guides)} files")
        else:
            print(f"  ⚠️  general_guides/ not found at {GENERAL_GUIDES_DIR}")
        
        if business_exists:
            guides = list(BUSINESS_GUIDES_DIR.glob("*.md"))
            print(f"  ✅ business_guides/: {len(guides)} files")
        else:
            print(f"  ⚠️  business_guides/ not found at {BUSINESS_GUIDES_DIR}")
        
        return general_exists or business_exists
    except Exception as e:
        print(f"  ❌ Knowledge base check failed: {e}")
        return False

def check_dependencies():
    """Verify required packages are available."""
    print("\n🔍 Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "chromadb",
        "sentence_transformers",
        "huggingface_hub",
        "dotenv",
        "yaml",
        "pydantic",
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"  ❌ {package} (install with: pip install {package})")
    
    return len(missing) == 0

def main():
    """Run all checks."""
    print("=" * 60)
    print("ShopSpace AI Business Advisor - Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Project Structure", check_structure),
        ("Python Imports", check_imports),
        ("Knowledge Base", check_knowledge_base),
        ("Dependencies", check_dependencies),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check failed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All checks passed! You're ready to:")
        print("  1. Edit .env with your HF_TOKEN")
        print("  2. Run: python -m app.ingest")
        print("  3. Run: uvicorn app.main:app --reload --port 8000")
        print("  4. Visit: http://localhost:8000/docs")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
