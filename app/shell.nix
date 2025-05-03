{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python3
    python3Packages.pip
    python3Packages.virtualenv
    
    # System dependencies that might be needed by Python packages
    openssl
    libffi
    zlib
    libxml2
    libxslt
    postgresql
    sqlite
    
    # C++ dependencies for Google Cloud libraries
    stdenv.cc.cc.lib
    
    # Development tools
    gnumake
    gcc
  ];
  
  shellHook = ''
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
    
    echo "Fionntan - NixOS Development Environment"
    echo "Run 'python main.py' to start the application"
  '';
}
