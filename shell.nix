with import <nixpkgs> {};

pkgs.mkShell {
  buildInputs = with pkgs; [
    xorg.libX11
    libGL
    gcc
    cmake
    gfortran
    gsl
    doxygen
    anki
    pandoc
    gifsicle
    pkgs.texlive.combined.scheme-full
    pkgs.biber
  ];

  packages = [
  (pkgs.python3.withPackages(python-pkgs: [
    python-pkgs.jupyter
    python-pkgs.ipykernel
    python-pkgs.pandas
    python-pkgs.imageio
    python-pkgs.marimo
    python-pkgs.networkx
  ]))
  ];

  shellHook = ''
    echo "### Welcome to Fionntan! ###"
    '';

}
