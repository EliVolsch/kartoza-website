{
  description = "Kartoza Website";

  # nixConfig = {
  #   extra-substituters = [ "https://example.cachix.org" ];
  #   extra-trusted-public-keys = [ "example.cachix.org-1:xxxx=" ];
  # };

  inputs = {
    nixpkgs-version.url = "github:QGIS/qgis-nixpkgs-version";
    nixpkgs.follows = "nixpkgs-version/nixpkgs-25-05";
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs =
    { self, nixpkgs, nixpkgs-unstable, ... }:

    let
      # Flake system
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;

      nixpkgsFor = forAllSystems (
        system:
        import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        }
      );

      # nixpkgs-unstable for packages with security fixes
      nixpkgsUnstableFor = forAllSystems (
        system:
        import nixpkgs-unstable {
          inherit system;
          config.allowUnfree = true;
        }
      );

    in
    {
      #
      ### PACKAGES
      #

      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgsFor.${system};
        in
        rec {
          website = pkgs.callPackage ./nix/package.nix { };
          default = website;
        }
      );

      #
      ### APPS
      #

      apps = forAllSystems (
        system:
        let
          pkgs = nixpkgsFor.${system};
          inherit (nixpkgs) lib;

          wwwLauncher = pkgs.writeShellApplication {
            name = "website";
            runtimeInputs = [ pkgs.python3 ];
            text = ''
              exec ${lib.getExe pkgs.python3} \
                -m http.server 8000 \
                -d ${self.packages.${system}.website}/public_www/
            '';
          };
        in
        rec {
          website = {
            type = "app";
            program = "${wwwLauncher}/bin/website";
          };
          default = website;
        }
      );

      #
      ### SHELLS
      #

      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgsFor.${system};
          pkgsUnstable = nixpkgsUnstableFor.${system};
          # Use unstable Python packages for security fixes (Pillow CVE-2026-25990)
          pythonEnv = pkgsUnstable.python3.withPackages (ps: with ps; [
            icalendar # Calendar handling
            requests # HTTP requests - for ERPNext API
            pyyaml # YAML generation
            pillow # Image processing (12.1.0 - patched for CVE-2026-25990)
            stripe # Donor management
            beautifulsoup4 # HTML parsing - for content comparison
            html2text # HTML to markdown conversion
            python-dateutil # Date parsing
            tabulate # Nice table output
          ]);
        in
        {
          # Development environment
          default = pkgs.mkShell {
            packages = [
              pkgs.hugo # Hugo for building the website
              pkgs.vscode # VSCode for development
              pythonEnv # Python with all packages from unstable
              pkgs.gnumake # GNU Make for build automation
            ];
            shellHook = ''
              export DIRENV_LOG_FORMAT=
              echo "-----------------------"
              echo "🌈 Your Hugo Dev Environment is ready."
              echo "It provides hugo and vscode for use with the Kartoza Website Project"
              echo ""
              echo "🪛 VSCode:"
              echo "--------------------------------"
              echo "Start vscode like this:"
              echo ""
              echo "./vscode.sh"
              echo ""
              echo "🪛 Hugo:"
              echo "--------------------------------"
              echo "Start Hugo like this:"
              echo ""
              echo "hugo server"
              echo "-----------------------"
            '';
          };
        }
      );
    };
}
