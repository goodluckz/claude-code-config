---
name: nix-darwin
description: nix-darwin configuration management commands and workflows
---

# nix-darwin Configuration Guide

## Quick Commands

### Rebuild and Apply Configuration
```bash
# Full rebuild with sudo (required for system changes)
sudo darwin-rebuild switch --flake /Users/zhaoliang/LocalRepos/nix-darwin#zhaos-MacBook-Pro

# From within the repository directory
sudo darwin-rebuild switch --flake .#zhaos-MacBook-Pro

# Build without applying (preview/test)
darwin-rebuild build --flake .#zhaos-MacBook-Pro
```

### Update Flake Inputs
```bash
# Update all inputs (nixpkgs, home-manager, nix-darwin, etc.)
nix flake update

# Update specific input only
nix flake update nixpkgs
nix flake update home-manager

# Check current input versions
nix flake metadata
```

### Home Manager Only
```bash
home-manager switch --flake .#zhaoliang
```

## Configuration Files

| File | Purpose |
|------|---------|
| `flake.nix` | Flake inputs and system outputs |
| `configuration.nix` | System packages, Homebrew, macOS defaults |
| `home.nix` | User programs, shell config, dotfiles |
| `flake.lock` | Locked dependency versions |

## Adding Packages

### System Packages (configuration.nix)
```nix
environment.systemPackages = with pkgs; [
  vim
  git
  newPackage  # Add here
];
```

### Homebrew Brews (configuration.nix)
```nix
homebrew.brews = [
  "gh"
  "newbrew"  # Add here
];
```

### Homebrew Casks (configuration.nix)
```nix
homebrew.casks = [
  "raycast"
  "newcask"  # Add here
];
```

### Home Manager Programs (home.nix)
```nix
programs.newprogram = {
  enable = true;
  # Additional config...
};
```

## Searching for Packages

```bash
# Search nixpkgs
nix search nixpkgs packagename

# Or use the web interface
# https://search.nixos.org/packages

# Search Homebrew
brew search packagename
```

## Troubleshooting

### Flake Parsing Errors
```bash
nix flake check
```

### Garbage Collection
```bash
# Remove old generations
nix-collect-garbage -d

# Remove generations older than 30 days
sudo nix-collect-garbage --delete-older-than 30d
```

### Rollback
```bash
# List generations
darwin-rebuild --list-generations

# Switch to previous generation
sudo darwin-rebuild switch --rollback
```

## Workflow

1. Edit `configuration.nix` or `home.nix`
2. Test build: `darwin-rebuild build --flake .#zhaos-MacBook-Pro`
3. Apply: `sudo darwin-rebuild switch --flake .#zhaos-MacBook-Pro`
4. Commit changes: `git add . && git commit -m "description"`

## Apps Not Available via Nix or Homebrew

These apps must be installed manually (Mac App Store or direct download):

| App | Reason | Install Method |
|-----|--------|----------------|
| Ulysses | Mac App Store only | `mas install 1225570693` |
| MacDroid | Not in Homebrew | Direct download from official site |
| Moomoo | Not in Homebrew | Direct download or App Store |

To install Mac App Store apps via CLI:
```bash
# Install mas (Mac App Store CLI)
brew install mas

# Search for an app
mas search "app name"

# Install by App ID
mas install <app-id>

# List installed apps
mas list
```
