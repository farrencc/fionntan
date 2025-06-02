#!/usr/bin/env python3
"""
Immediate validation script for Fionntán
Run this to test what's working right now before external service integration
"""

import os
import sys
import subprocess
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")

def test_environment():
    """Test basic environment setup"""
    print_section("ENVIRONMENT SETUP")
    
    # Check Python version
    python_version = sys.version_info
    python_ok = python_version >= (3, 8)
    print_result("Python version", python_ok, f"Python {python_version.major}.{python_version.minor}")
    
    # Check if we're in project root
    has_main_py = (project_root / "main.py").exists()
    has_app_dir = (project_root / "app").exists()
    project_structure_ok = has_main_py and has_app_dir
    print_result("Project structure", project_structure_ok, "main.py and app/ directory found")
    
    # Check for basic files
    important_files = [
        "app/__init__.py",
        "app/models.py",
        "app/config.py",
        "tests/conftest.py"
    ]
    
    for file_path in important_files:
        exists = (project_root / file_path).exists()
        print_result(f"File: {file_path}", exists)
    
    return python_ok and project_structure_ok

def test_imports():
    """Test critical imports"""
    print_section("PYTHON IMPORTS")
    
    imports_to_test = [
        ("flask", "Flask"),
        ("sqlalchemy", "SQLAlchemy"),
        ("flask_jwt_extended", "JWTManager"),
        ("celery", "Celery"),
        ("arxiv", "arxiv module"),
        ("pytest", "pytest"),
        ("authlib", "Authlib"),
    ]
    
    all_imports_ok = True
    for module, description in imports_to_test:
        try:
            __import__(module)
            print_result(f"Import: {description}", True)
        except ImportError as e:
            print_result(f"Import: {description}", False, str(e))
            all_imports_ok = False
    
    return all_imports_ok

def test_app_creation():
    """Test Flask app creation"""
    print_section("FLASK APP CREATION")
    
    try:
        os.chdir(project_root)
        from app import create_app
        
        # Test development config
        app = create_app('development')
        app_created = app is not None
        print_result("Flask app creation", app_created)
        
        # Test config loading
        has_secret_key = bool(app.config.get('SECRET_KEY'))
        print_result("Secret key configured", has_secret_key)
        
        # Test database config
        has_db_uri = bool(app.config.get('SQLALCHEMY_DATABASE_URI'))
        print_result("Database URI configured", has_db_uri)
        
        return app_created and has_secret_key and has_db_uri
        
    except Exception as e:
        print_result("Flask app creation", False, str(e))
        return False

def test_database():
    """Test database operations"""
    print_section("DATABASE OPERATIONS")
    
    try:
        from app import create_app, db
        from app.models import User, UserPreference, Podcast
        
        app = create_app('development')
        with app.app_context():
            # Test database connection
            try:
                db.create_all()
                print_result("Database tables creation", True)
            except Exception as e:
                print_result("Database tables creation", False, str(e))
                return False
            
            # Test user model
            try:
                user = User(
                    email='test@validation.com',
                    google_id='test-validation-123',
                    name='Test User'
                )
                db.session.add(user)
                db.session.commit()
                print_result("User model operations", True)
                
                # Test preferences
                pref = UserPreference(
                    user_id=user.id,
                    topics=['test topic'],
                    max_results=10
                )
                db.session.add(pref)
                db.session.commit()
                print_result("UserPreference model operations", True)
                
                # Cleanup
                db.session.delete(pref)
                db.session.delete(user)
                db.session.commit()
                
                return True
                
            except Exception as e:
                print_result("Database model operations", False, str(e))
                return False
                
    except Exception as e:
        print_result("Database test setup", False, str(e))
        return False

def test_arxiv_service():
    """Test ArXiv service with real API"""
    print_section("ARXIV SERVICE (Real API)")
    
    try:
        from app import create_app
        from app.services.arxiv_service import ArxivService
        
        app = create_app('development')
        with app.app_context():
            service = ArxivService()
            
            # Test basic search
            try:
                papers, total = service.search_papers(
                    topics=['machine learning'],
                    max_results=1
                )
                print_result("ArXiv search", total > 0, f"Found {total} papers")
                
                if papers:
                    paper = papers[0]
                    has_required_fields = all(
                        field in paper for field in ['id', 'title', 'authors', 'abstract']
                    )
                    print_result("Paper data structure", has_required_fields)
                    
                    # Test get by ID
                    paper_id = paper['id']
                    retrieved_paper = service.get_paper_by_id(paper_id)
                    print_result("Get paper by ID", retrieved_paper is not None)
                    
                    return True
                else:
                    print_result("ArXiv data retrieval", False, "No papers returned")
                    return False
                    
            except Exception as e:
                print_result("ArXiv API call", False, str(e))
                return False
                
    except Exception as e:
        print_result("ArXiv service setup", False, str(e))
        return False

def test_api_endpoints():
    """Test API endpoint structure"""
    print_section("API ENDPOINTS")
    
    try:
        from app import create_app
        
        app = create_app('development')
        client = app.test_client()
        
        # Test health endpoint
        response = client.get('/api/v1/health')
        health_ok = response.status_code == 200
        print_result("Health endpoint", health_ok, f"Status: {response.status_code}")
        
        # Test ArXiv categories endpoint (might need auth, but test structure)
        response = client.get('/api/v1/arxiv/categories')
        # This might return 401 due to auth, but 404 would be a structure problem
        categories_structure_ok = response.status_code in [200, 401, 422]
        print_result("ArXiv categories endpoint exists", categories_structure_ok)
        
        return health_ok
        
    except Exception as e:
        print_result("API endpoint test", False, str(e))
        return False

def test_test_suite():
    """Run the actual test suite"""
    print_section("TEST SUITE EXECUTION")
    
    try:
        # Stay in project root - tests directory is at root level
        original_dir = os.getcwd()
        os.chdir(project_root)
        
        # Check if tests directory exists at project root
        tests_dir = project_root / "tests"
        if not tests_dir.exists():
            print_result("Tests directory", False, "tests/ directory not found at project root")
            return False
        
        print_result("Tests directory found", True, f"At {tests_dir}")
        
        # Run pytest from project root
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Restore original directory
        os.chdir(original_dir)
        
        test_suite_passed = result.returncode == 0
        print_result("Test suite execution", test_suite_passed)
        
        if not test_suite_passed:
            print("   Test output (last 10 lines):")
            stdout_lines = result.stdout.split('\n')
            for line in stdout_lines[-10:]:
                if line.strip():
                    print(f"   {line}")
            
            if result.stderr:
                print("   Test errors:")
                stderr_lines = result.stderr.split('\n')
                for line in stderr_lines[-5:]:
                    if line.strip():
                        print(f"   {line}")
            
        return test_suite_passed
        
    except subprocess.TimeoutExpired:
        print_result("Test suite execution", False, "Timeout after 60 seconds")
        return False
    except Exception as e:
        print_result("Test suite execution", False, str(e))
        return False

def test_frontend_basics():
    """Test frontend basics"""
    print_section("FRONTEND BASICS")
    
    # Check if package.json exists
    package_json = project_root / "package.json"
    if not package_json.exists():
        print_result("package.json", False, "File not found")
        return False
    
    print_result("package.json", True)
    
    # Check if src directory exists
    src_dir = project_root / "src"
    if not src_dir.exists():
        print_result("src directory", False, "Directory not found")
        return False
    
    print_result("src directory", True)
    
    # Check key frontend files
    frontend_files = [
        "src/App.js",
        "src/index.js",
        "src/contexts/AuthContext.js",
        "src/pages/Login.js"
    ]
    
    frontend_ok = True
    for file_path in frontend_files:
        exists = (project_root / file_path).exists()
        print_result(f"File: {file_path}", exists)
        if not exists:
            frontend_ok = False
    
    return frontend_ok

def main():
    """Run all validation tests"""
    print("🚀 FIONNTÁN FOUNDATION VALIDATION")
    print(f"Running from: {project_root}")
    
    tests = [
        ("Environment Setup", test_environment),
        ("Python Imports", test_imports),
        ("Flask App Creation", test_app_creation),
        ("Database Operations", test_database),
        ("ArXiv Service", test_arxiv_service),
        ("API Endpoints", test_api_endpoints),
        ("Test Suite", test_test_suite),
        ("Frontend Basics", test_frontend_basics),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print_result(f"{test_name} (EXCEPTION)", False, str(e))
            results[test_name] = False
    
    # Summary
    print_section("VALIDATION SUMMARY")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 OVERALL SCORE: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 EXCELLENT! Your foundation is solid.")
        print("✅ You can proceed with confidence to external service integration.")
    elif passed >= total * 0.8:
        print("\n👍 GOOD! Most tests passed.")
        print("⚠️  Fix the failing tests before proceeding.")
    else:
        print("\n⚠️  NEEDS WORK! Several critical tests failed.")
        print("🔧 Address these issues before adding external services.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
