<p align="center">
  <a href="https://kartoza.com">
    <img src="static/img/kartoza-logo.png" alt="Kartoza Logo" width="300">
  </a>
</p>

<h1 align="center">Kartoza Website</h1>

<p align="center">
  <strong>A Happy Life is a Mappy Life</strong>
</p>

<p align="center">
  <em>Official website for <a href="https://kartoza.com">Kartoza</a> - Open Source Geospatial Experts</em>
</p>

---

<p align="center">
  <!-- CI/CD Status -->
  <a href="https://github.com/kartoza/kartoza-website/actions/workflows/github-pages.yml">
    <img src="https://github.com/kartoza/kartoza-website/actions/workflows/github-pages.yml/badge.svg" alt="Deploy to GitHub Pages">
  </a>
  <a href="https://github.com/kartoza/kartoza-website/actions/workflows/nix-build.yml">
    <img src="https://github.com/kartoza/kartoza-website/actions/workflows/nix-build.yml/badge.svg" alt="Nix Build">
  </a>
  <a href="https://github.com/kartoza/kartoza-website/actions/workflows/playwright-e2e.yml">
    <img src="https://github.com/kartoza/kartoza-website/actions/workflows/playwright-e2e.yml/badge.svg" alt="E2E Tests">
  </a>
</p>

<p align="center">
  <!-- Tech Stack -->
  <img src="https://img.shields.io/badge/Hugo-0.147+-FF4088?style=flat&logo=hugo&logoColor=white" alt="Hugo">
  <img src="https://img.shields.io/badge/Bulma-CSS-00D1B2?style=flat&logo=bulma&logoColor=white" alt="Bulma CSS">
  <img src="https://img.shields.io/badge/Nix-Flakes-5277C3?style=flat&logo=nixos&logoColor=white" alt="Nix Flakes">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white" alt="Docker">
</p>

<p align="center">
  <!-- Project Health -->
  <a href="https://github.com/kartoza/kartoza-website/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/kartoza/kartoza-website?style=flat" alt="License">
  </a>
  <a href="https://github.com/kartoza/kartoza-website/commits/main">
    <img src="https://img.shields.io/github/last-commit/kartoza/kartoza-website?style=flat" alt="Last Commit">
  </a>
  <a href="https://github.com/kartoza/kartoza-website/issues">
    <img src="https://img.shields.io/github/issues/kartoza/kartoza-website?style=flat" alt="Open Issues">
  </a>
  <a href="https://github.com/kartoza/kartoza-website/pulls">
    <img src="https://img.shields.io/github/issues-pr/kartoza/kartoza-website?style=flat" alt="Pull Requests">
  </a>
</p>

<p align="center">
  <!-- Security -->
  <img src="https://img.shields.io/badge/Security-Audited-success?style=flat&logo=shieldsdotio" alt="Security Audited">
  <img src="https://img.shields.io/badge/nginx-1.28.2-009639?style=flat&logo=nginx&logoColor=white" alt="nginx">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
</p>

---

## About Kartoza

<img align="right" src="static/img/kartoza-logo-modern.svg" width="120">

**Kartoza** is a global Free and Open Source GIS (FOSS GIS) service provider registered in South Africa and Portugal. We use GIS software to address location-related challenges for individuals, businesses, and governments worldwide.

### Our Vision

> Enable a world where spatial decision making tools are **universal**, **accessible** and **affordable** for everyone for the benefit of the planet and people.

### What We Do

- Custom GIS software development
- Geospatial data management & analysis
- Training & capacity building
- Support & maintenance for open source GIS

---

## Technology Stack

| Category | Technology |
|----------|------------|
| **Static Site Generator** | [Hugo](https://gohugo.io/) (Extended) |
| **CSS Framework** | [Bulma](https://bulma.io/) |
| **Theme** | Custom `hugo-bulma-blocks-theme` |
| **Development Environment** | [Nix Flakes](https://nixos.wiki/wiki/Flakes) |
| **Container Runtime** | Docker + nginx |
| **CI/CD** | GitHub Actions |
| **Testing** | Playwright E2E |

---

## Quick Start

### Using Nix (Recommended)

```bash
# Enter the development environment
nix develop

# Start the development server
hugo server
```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Manual Setup

```bash
# Prerequisites: Hugo extended version
hugo version  # Should show "extended"

# Start development server
hugo server -D

# Build for production
hugo --minify
```

The site will be available at `http://localhost:1313`

---

## Project Structure

```
Kartoza-Hugo/
├── content/               # Markdown content files
│   ├── about/             # About page
│   ├── apps/              # Mobile and web applications
│   ├── blog/              # Blog posts
│   ├── careers/           # Job listings
│   ├── gallery/           # Image gallery
│   ├── portfolio/         # Project portfolio
│   ├── solutions/         # Solutions and services
│   ├── the_team/          # Team members
│   └── training-courses/  # Training offerings
├── layouts/               # Custom Hugo templates
├── static/                # Static assets (images, etc.)
├── themes/                # Hugo theme
├── deployment/            # Docker & nginx configs
├── scripts/               # Automation scripts
└── flake.nix              # Nix development environment
```

---

## Development

### Available Commands

| Command | Description |
|---------|-------------|
| `hugo server` | Start development server with live reload |
| `hugo server -D` | Include draft content |
| `hugo --minify` | Build optimized production site |
| `nix build` | Build site using Nix |
| `nix run` | Build and serve site |

### CI/CD Workflows

| Workflow | Purpose |
|----------|---------|
| `github-pages.yml` | Deploy to GitHub Pages |
| `nix-build.yml` | Verify Nix build |
| `playwright-e2e.yml` | End-to-end tests |
| `update-contributors.yml` | Sync contributor data |
| `update-donors.yml` | Sync donor information |
| `update-gh-sponsors.yml` | Sync GitHub Sponsors |

---

## Security

This project follows security best practices:

- **Dependency Auditing**: Regular CVE scanning of all dependencies
- **Container Security**: Hardened nginx configuration with non-root user
- **Automated Updates**: nixpkgs-unstable for latest security patches
- **HTTPS Enforced**: All deployments use TLS

See our security practices in [`flake.nix`](./flake.nix) and [`Dockerfile`](./deployment/docker/Dockerfile).

---

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
4. **Make** your changes
5. **Test** locally with `hugo server`
6. **Commit** your changes (`git commit -m 'Add amazing feature'`)
7. **Push** to the branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

### Code Style

- Use Prettier for formatting (config in `.prettierrc.json`)
- Follow Hugo template best practices
- Keep commits atomic and well-described

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](./LICENSE) file for details.

---

## Contact

<p align="center">
  <a href="https://kartoza.com">
    <img src="https://img.shields.io/badge/Website-kartoza.com-00A86B?style=for-the-badge&logo=google-chrome&logoColor=white" alt="Website">
  </a>
  <a href="mailto:info@kartoza.com">
    <img src="https://img.shields.io/badge/Email-info@kartoza.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white" alt="Email">
  </a>
  <a href="https://github.com/kartoza">
    <img src="https://img.shields.io/badge/GitHub-kartoza-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
  </a>
</p>

<p align="center">
  <a href="https://www.linkedin.com/company/kartoza">
    <img src="https://img.shields.io/badge/LinkedIn-Kartoza-0A66C2?style=flat&logo=linkedin&logoColor=white" alt="LinkedIn">
  </a>
  <a href="https://twitter.com/kartaborolong">
    <img src="https://img.shields.io/badge/Twitter-@kartaborolong-1DA1F2?style=flat&logo=twitter&logoColor=white" alt="Twitter">
  </a>
  <a href="https://www.youtube.com/@kartaborolong">
    <img src="https://img.shields.io/badge/YouTube-Kartoza-FF0000?style=flat&logo=youtube&logoColor=white" alt="YouTube">
  </a>
</p>

---

<p align="center">
  Made with 💗 by <a href="https://kartoza.com">Kartoza</a> |
  <a href="https://github.com/sponsors/kartoza">Donate!</a> |
  <a href="https://github.com/kartoza/kartoza-website">GitHub</a>
</p>

<p align="center">
  <sub>🌍 Empowering the world with Open Source Geospatial Solutions since 2008</sub>
</p>
