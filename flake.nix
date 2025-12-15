{
  description = "BitBucketConverter (Python 3)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
  let
    systems = [ "x86_64-linux" "aarch64-darwin" ];

    forAllSystems = f:
      nixpkgs.lib.genAttrs systems (system:
        f (import nixpkgs { inherit system; })
      );
  in
  {
    packages = forAllSystems (pkgs: {
      default = pkgs.writeShellScriptBin "BitBucketConverter" ''
        exec ${pkgs.python3.withPackages (ps: [ ps.pycurl ])}/bin/python \
          ${./BitBucketConverter.py} "$@"
      '';
    });

    devShells = forAllSystems (pkgs: {
      default = pkgs.mkShell {
        packages = [
          (pkgs.python3.withPackages (ps: [ ps.pycurl ]))
        ];
      };
    });
  };
}

