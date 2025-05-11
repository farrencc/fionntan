# Create and activate virtual environment
    if [ ! -d "venv" ]; then
      echo "Creating virtual environment..."
      python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # Install basic packages to bootstrap the environment
    pip install --upgrade pip setuptools wheel
    
    # Install packages if requirements.txt exists
    if [ -f requirements.txt ]; then
      echo "Installing dependencies from requirements.txt..."
      pip install -r requirements.txt
    fi
    
    # Environment variables
    export FLASK_APP=main.py
    export FLASK_ENV=development
    export PYTHONPATH=$PWD:$PYTHONPATH
    
    # Explicitly set library path for C++ libraries
    export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH
    
    echo "Fionntan - Development Environment"
    echo "Run 'python main.py' to start the application"