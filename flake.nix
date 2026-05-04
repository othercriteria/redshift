{
  description = "Toy model for untangling Doppler and cosmological redshift";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python314.withPackages (ps: with ps; [
          numpy
          scipy
          matplotlib
          pandas
          cmdstanpy
        ]);
        tex = pkgs.texlive.combine {
          inherit (pkgs.texlive)
            scheme-medium
            ;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            python
            pkgs.cmdstan
            pkgs.pandoc
            pkgs.just
            pkgs.git-lfs
            pkgs.gh
            tex
          ];

          shellHook = ''
            # cmdstanpy locates the CmdStan install via $CMDSTAN.
            # nixpkgs lays it out under $out/opt/cmdstan; adjust if a
            # future bump moves the path.
            export CMDSTAN=${pkgs.cmdstan}/opt/cmdstan
          '';
        };
      }
    );
}
