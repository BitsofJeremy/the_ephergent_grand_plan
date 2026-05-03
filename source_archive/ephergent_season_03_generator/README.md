# Ephergent Season 03 Story Generator

A sophisticated Flask-based story generation system for The Ephergent Universe Season 03. This production-ready application generates weekly episodic stories using Google's Gemini AI through a comprehensive multi-stage workflow including story generation, image creation, audio narration, video production, and automated publishing.

## 🚀 Features

- **Complete Workflow Pipeline**: Stories progress through 8 stages from topic to YouTube/blog publication
- **Character-Based Narration**: 12 unique Season 03 characters with distinct voices and specializations
- **Database-Driven Admin System**: Full admin portal for character and system configuration management
- **Advanced Media Generation**: Images (ComfyUI), audio (Kokoro TTS), and video (MoviePy) creation
- **Background Processing**: Scalable worker system with queue management and error recovery
- **User Authentication**: Admin users with API key management for secure operations
- **Story Archiving**: Complete archival system for preserving stories and media files
- **Professional Web Interface**: Bootstrap 5 responsive UI with real-time status updates
- **Admin REST API**: Comprehensive admin API with Swagger documentation (`/api/admin/`)
- **Episode Automation**: Auto-generate all 12 season episodes from story arc JSON
- **Production Ready**: Multi-environment support with comprehensive logging and monitoring

## 📋 Prerequisites

- Python 3.11 or higher
- Google Gemini API key (free from [Google AI Studio](https://makersuite.google.com/app/apikey))
- ComfyUI server for image generation (optional but recommended)
- Kokoro TTS server for audio generation (optional)
- `uv` package manager (recommended) or `pip`

## 🎯 Season 03 Character Roster

The system features 12 specialized characters for story narration:

1. **Pixel Paradox** (default) - Underground journalist leader
2. **A1 Assistant** - British AI tech expert
3. **Zephyr Glitch** - Reality hacker specialist
4. **Clive Stapler Informant** - Wise mentor stapler
5. **Luminara Usha** - Visual documentation specialist
6. **Om Kai** - Scientific meditation philosopher
7. **Nano Informant** - Street-smart information broker
8. **The Archivist** - Ancient mystery collector
9. **Verdantian Elder** - Environmental network coordinator
10. **Nocturne Aesthete** - Cultural critic and translator
11. **Baron Klaus von Gnomendorf** - Pompous tactical gnome
12. **Meatball Rottweiler** - Loyal comic relief companion

## 🚀 Quick Start

Run as root: 
```bash
sudo bash scripts/deploy_on_debian.sh --dest /opt/ephergent_season_03_generator --git git@github.com:ephergent/ephergent_season_03_generator.git --env /root/.env
```


### Bare‑metal VM deployment (recommended)

This project no longer uses Docker by default. The primary supported deployment method is a bare-metal (or VM) install on a minimal Debian/Ubuntu VM — this is simpler to run in production for single-host deployments and avoids container complexity.

High-level steps:

1. Provision a minimal VM (Debian 12/Ubuntu 22.04 or newer).
2. Install system packages (Python, git, build tools).
3. Clone the repository on the VM, create a virtualenv, and install dependencies.
4. Configure environment variables in `.env`.
5. Run DB migrations and create an admin user.
6. Install the provided `systemd` service units and enable them.

Example step‑by‑step (run as a privileged user on the VM):

```bash
# Update & basic packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl build-essential python3.11 python3.11-venv python3-pip

# Create deploy user (optional, recommended)
sudo adduser --disabled-password --gecos "" ephergent
sudo usermod -aG sudo ephergent
sudo -i -u ephergent bash

# Clone the repository
cd /opt
git clone git@github.com:ephergent/ephergent_season_03_generator.git ephergent_season_03_generator
cd ephergent_season_03_generator

# Recommended: use uv to install dependencies (creates .venv)
# If you use the included deploy script, it will perform similar steps for you
uv sync

# Alternative: create venv and install with pip if you don't use 'uv'
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
# Install from pyproject (preferred) or requirements if present
python -m pip install -e .

# Copy and edit environment file
cp .env.example .env
# Edit `.env` with your secrets (GEMINI_API_KEY, DB URL, etc.)

# Run database migrations
python scripts/run_migrations.py

# Create an admin user (interactive)
python manage_auth.py create-admin-user

# (Optional) Run a quick sanity check locally
source .venv/bin/activate
python main.py &
curl http://localhost:5000/api/v1/health/

# Install systemd service files (example)
sudo tee /etc/systemd/system/ephergent-web.service >/dev/null <<'SERVICE'
[Unit]
Description=Ephergent Season 03 Web Application
After=network.target postgresql.service

[Service]
Type=simple
User=ephergent
WorkingDirectory=/opt/ephergent_season_03_generator
Environment=FLASK_ENV=production
Environment=FLASK_DEBUG=False
ExecStart=/opt/ephergent_season_03_generator/.venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

sudo tee /etc/systemd/system/ephergent-worker.service >/dev/null <<'SERVICE'
[Unit]
Description=Ephergent Season 03 Background Worker
After=network.target postgresql.service

[Service]
Type=simple
User=ephergent
WorkingDirectory=/opt/ephergent_season_03_generator
Environment=FLASK_ENV=production
ExecStart=/opt/ephergent_season_03_generator/.venv/bin/python worker.py --continuous
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

# Enable & start services
sudo systemctl daemon-reload
sudo systemctl enable --now ephergent-web ephergent-worker

# Check logs
sudo journalctl -u ephergent-worker -f
# Or check the web service
sudo journalctl -u ephergent-web -f
```

Notes and best practices

- SSH keys: use SSH keys for `git clone` (or use an HTTPS clone with a deploy token).
- Ports: the web app binds to the configured host/port in `main.py` or your WSGI server. If you use a reverse proxy (nginx), point it to the local port and enable TLS.
- Virtualenv location: this guide uses `.venv` at the repo root. Adjust `ExecStart` paths in systemd units if you place the venv elsewhere.
- Environment: ensure the `.env` is secured and contains required variables (GEMINI_API_KEY, DATABASE_URL, SECRET_KEY, etc.).
- Logs: systemd captures stdout/stderr; you can also configure FileHandler in the application with a path set in `.env` (LOG_FILE).
- If you prefer a non-root deploy user, ensure that user has permissions for the repo and media directories.

When to use the included `scripts/deploy_on_debian.sh`

- The repo includes `scripts/deploy_on_debian.sh` which automates many of the above steps (creating directories, cloning, and wiring environment files). If you prefer a scripted install, run that script as root and pass `--env` to point to your `.env`.


### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd ephergent_season_03_generator

# Install dependencies with uv (creates .venv automatically)
uv sync

# Activate the virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

### 2. Configure Environment

```bash
# Copy the example configuration
cp .env.example .env

# Edit the configuration file
nano .env  # or your preferred editor
```

**Required: Set your Gemini API Key**
```bash
# In your .env file:
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Optional external services:
COMFYUI_URL=http://comfyui.home.test  # For image generation
KOKORO_URL=http://127.0.0.1:8880/v1   # For audio generation
```

### 3. Start the Application

```bash
# Terminal 1: Start the web server
python main.py
# or with uv run (no activation needed)
# uv run python main.py
```

### 4. Start the Worker (Required!)

```bash
# Terminal 2: Start the story processing worker
python worker.py --continuous
# or with uv run
# uv run python worker.py --continuous
```

### 5. Create Admin User

```bash
# Create your first admin user
python manage_auth.py create-admin-user
```

## 🔄 Complete Workflow System

Stories progress through these stages:

```
Topic → QUEUED → STORY_GENERATION → TITLE_GENERATION → IMAGE_GENERATION →
AUDIO_GENERATION → VIDEO_GENERATION → YOUTUBE_UPLOAD → GHOST_PUBLISHING → COMPLETED
```

### Workflow Stages:
1. **QUEUED** 🎯 - Story submitted, waiting for processing
2. **STORY_GENERATION** 📝 - AI creating story content with character narration
3. **TITLE_GENERATION** 📰 - AI generating an engaging title
4. **IMAGE_GENERATION** 🎨 - AI-generated illustrations via ComfyUI
5. **AUDIO_GENERATION** 🎵 - Character voice narration via Kokoro TTS
6. **VIDEO_GENERATION** 📹 - Video composition with images and audio
7. **YOUTUBE_UPLOAD** 📺 - Automated YouTube publishing
8. **GHOST_PUBLISHING** 📝 - Blog post creation and publishing
9. **COMPLETED** ✅ - Story published and ready

## 🎯 Key Features

### Character Management
- **Character Profile Generation**: Automated image generation for all characters
- **Character APIs**: REST endpoints for character management and image regeneration
- **Voice Configurations**: Unique voice settings for each character using Kokoro TTS
- **Specialized Topics**: Each character has expertise in specific story types

### Story Archiving
- **Complete Archival**: Stories archived with all media files (markdown, images, audio, video)
- **Archive API**: REST endpoints for archiving operations
- **CLI Tools**: Command-line interface for batch archiving
- **Organized Storage**: Date-based archive directory structure

### Authentication & Security
- **User Management**: Admin users with role-based permissions
- **API Keys**: Secure API key generation with rate limiting
- **Protected Endpoints**: Authentication required for administrative operations
- **Session Management**: Flask-Login integration for web interface

### Media Generation Pipeline
- **Image Generation**: ComfyUI integration with FLUX models and LoRA configurations
- **Audio Generation**: Multi-character TTS with voice mixing capabilities
- **Video Production**: MoviePy-based composition with images and narration
- **Publishing**: Automated YouTube uploads and Ghost blog publishing

## 📚 Usage Guide

### Web Interface

#### Admin Portal (`/admin/`) **✨ NEW**
- **Dashboard**: Real-time statistics, quick actions, recent task monitoring
- **Character Management**: CRUD operations for all 12 characters
  - Edit personality prompts, voice models, AI settings
  - Manage topics, tags, and profile images
  - Version history tracking for all changes
  - Bulk image generation and character activation/deactivation
- **System Configuration**: Manage universe prompts and system settings
  - Category-based organization (universe_prompts, api_settings, media_settings)
  - Type-aware value editing (string, JSON, markdown, int, float, bool)
  - Version tracking for configuration changes
- **Admin Tasks**: Monitor background operations
  - Real-time status with progress bars
  - Task cancellation and error handling
  - Filter by status (pending, running, completed, failed)

Access admin portal at: `http://localhost:5000/admin/` (requires admin login)

#### Story Generation (`/generate`)
- Submit story topics with character selection
- Customize genre, tone, and word count
- Real-time progress tracking

#### Story Archive (`/stories`)
- View all generated stories
- Archive management and download
- Story statistics and analytics

### REST API

The system provides a comprehensive REST API with Swagger documentation:

#### Public API
- **Stories API** (`/api/v1/stories/`) - Story management and generation
- **Characters API** (`/api/v1/characters/`) - Character management and image generation
- **Archive API** (`/api/v1/archive/`) - Story archiving operations
- **Workflow API** (`/api/v1/workflow/`) - Workflow status and management
- **Health API** (`/api/v1/health/`) - System health monitoring

Access API documentation at: `http://localhost:5000/api/v1/swagger`

#### Admin API **✨ NEW** (requires authentication)
- **Admin Characters API** (`/api/admin/characters/`) - Full CRUD operations
  - List all characters (with inactive filter)
  - Create, update, delete characters
  - Version history retrieval
  - Profile image regeneration
- **Admin Config API** (`/api/admin/config/`) - System configuration management
  - List all configurations by category
  - Create, update, delete configs
  - Version tracking and history
- **Admin Tasks API** (`/api/admin/tasks/`) - Administrative task management
  - Create and monitor background tasks
  - Cancel running tasks
  - Task status and results

Access admin API documentation at: `http://localhost:5000/api/admin/swagger`

### Command-Line Tools

#### Character Image Generation
```bash
# Generate images for all characters
python scripts/character_profile_generator_s3.py

# Generate for specific character
python scripts/character_profile_generator_s3.py --character pixel_paradox

# Force regeneration
python scripts/character_profile_generator_s3.py --force
```

#### Story Archiving
```bash
# Archive all completed stories
python scripts/archive_stories.py --archive-all

# Archive specific story
python scripts/archive_stories.py --story 123

# Show archive status
python scripts/archive_stories.py --status
```

#### User Management
```bash
# Create admin user
python manage_auth.py create-admin-user

# Create API key
python manage_auth.py create-api-key --user-id 1 --name "automation-key"

# List users and keys
python manage_auth.py list-users
python manage_auth.py list-api-keys
```

#### Episode Automation **✨ NEW**
```bash
# Check season arc status
python scripts/generate_season.py --status

# Queue specific episode
python scripts/generate_season.py --episode 5

# Queue all 12 episodes
python scripts/generate_season.py --queue-all --priority sequential

# Queue with different priority modes
python scripts/generate_season.py --queue-all --priority batch      # All priority 100
python scripts/generate_season.py --queue-all --priority reverse   # Reverse order
```

#### Data Migration **✨ NEW**
```bash
# Check migration status
python scripts/migrate_to_database.py --status

# Migrate all data (characters + universe prompt)
python scripts/migrate_to_database.py

# Selective migration
python scripts/migrate_to_database.py --characters-only
python scripts/migrate_to_database.py --universe-only
```

## ⚙️ Configuration

### Required Settings
```bash
# Google Gemini API key (REQUIRED)
GEMINI_API_KEY=your_api_key_here
```

### External Services
```bash
# ComfyUI for image generation
COMFYUI_URL=http://comfyui.home.test

# Kokoro TTS for audio generation
KOKORO_URL=http://127.0.0.1:8880/v1

# YouTube API configuration
YOUTUBE_CLIENT_SECRET_FILE=client_secret.json

# Ghost blog publishing
GHOST_ADMIN_KEY=your_ghost_admin_key
GHOST_API_URL=https://yourblog.ghost.io
```

### Database Configuration
```bash
# Development (SQLite)
DATABASE_URL=sqlite:///stories.db

# Production (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/ephergent_s3
```

## 🏗️ Development

### Project Structure
```
ephergent_season_03_generator/
├── ephergent_generator/              # Main Flask application
│   ├── __init__.py                   # App factory
│   ├── models.py                     # Database models (Story, User, APIKey)
│   ├── main/                         # Web interface blueprint
│   ├── api/                          # REST API blueprints
│   │   ├── stories.py               # Story operations
│   │   ├── characters.py            # Character management
│   │   ├── archive.py               # Archive operations
│   │   └── workflow.py              # Workflow monitoring
│   ├── services/                     # Business logic services
│   │   ├── story_workflow_service.py # Main workflow orchestration
│   │   ├── gemini_service.py        # AI story generation
│   │   ├── comfyui_service.py       # Image generation
│   │   ├── audio_service.py         # TTS integration
│   │   ├── video_service.py         # Video composition
│   │   ├── youtube_service.py       # YouTube publishing
│   │   ├── ghost_service.py         # Blog publishing
│   │   ├── character_service.py     # Character management
│   │   ├── archive_service.py       # Story archiving
│   │   └── auth_service.py          # Authentication
│   ├── prompts/                      # Character and universe prompts
│   │   ├── personality_prompts_s3.json # Character definitions
│   │   └── characters/              # Individual character prompts
│   └── templates/                   # HTML templates
├── scripts/                         # Command-line utilities
│   ├── character_profile_generator_s3.py
│   ├── archive_stories.py
│   └── reporter_profile_image_generator.py
├── config.py                        # Configuration classes
├── main.py                          # Web application entry point
├── worker.py                        # Background worker
├── manage_auth.py                   # User management utility
└── CLAUDE.md                        # Development guide for Claude
```

### Database Models

#### Story Model
- Complete workflow state tracking
- JSON fields for media paths and metadata
- Session-based user tracking
- Integration with external publishing services

#### User Model
- Secure password hashing with bcrypt
- Role-based permissions (admin/user)
- API key relationship management
- Login tracking and session management

#### APIKey Model
- Secure key generation and hashing
- Rate limiting and usage tracking
- Permission-based access control
- Automatic expiration handling

## 🔧 Production Deployment

### Environment Setup
```bash
# Production environment
FLASK_ENV=production
FLASK_DEBUG=False

# Database
DATABASE_URL=postgresql://user:password@localhost/ephergent_s3

# Security
SECRET_KEY=your-super-secure-random-key

# External services URLs
COMFYUI_URL=http://your-comfyui-server:8188
KOKORO_URL=http://your-tts-server:8880/v1
```

### Systemd Services

Create service files for both the web application and worker:

```ini
# /etc/systemd/system/ephergent-web.service
[Unit]
Description=Ephergent Season 03 Web Application
After=network.target postgresql.service

[Service]
Type=simple
User=ephergent
WorkingDirectory=/opt/ephergent_season_03_generator
Environment=FLASK_ENV=production
ExecStart=/opt/ephergent_season_03_generator/.venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/ephergent-worker.service
[Unit]
Description=Ephergent Season 03 Background Worker
After=network.target postgresql.service

[Service]
Type=simple
User=ephergent
WorkingDirectory=/opt/ephergent_season_03_generator
Environment=FLASK_ENV=production
ExecStart=/opt/ephergent_season_03_generator/.venv/bin/python worker.py --continuous
Restart=always

[Install]
WantedBy=multi-user.target
```

### Cron Job for Weekly Stories
```bash
# Add to crontab for automated weekly story generation
# Runs every Saturday at 8 PM
0 20 * * 6 /opt/ephergent_season_03_generator/scripts/weekly_story_generator.py
```

## 🔍 Monitoring and Troubleshooting

### Health Monitoring
```bash
# Check system health
curl http://localhost:5000/api/v1/health/

# Check specific service health
curl http://localhost:5000/api/v1/health/services
```

### Queue Management
```bash
# Show queue status
python worker.py --status

# Clean up stuck workers
python worker.py --cleanup

# Process specific number of stories
python worker.py --max-stories 10
```

### Archive Management
```bash
# Show archive statistics
python scripts/archive_stories.py --status

# List archived stories
python scripts/archive_stories.py --list-archived

# Clean up invalid archives
curl -X POST http://localhost:5000/api/v1/archive/cleanup
```

## 📈 Roadmap & Future Enhancements

### Completed ✅
- Multi-stage story generation workflow
- Character-based narration system (12 unique Season 03 characters)
- Complete media generation pipeline (images, audio, video)
- Story archiving system with CLI tools
- User authentication and API keys
- REST API with Swagger documentation
- Command-line management tools
- **Database-driven admin system** (October 2025)
  - Character CRUD with version history
  - System configuration management
  - Admin REST API with Swagger
  - Professional Bootstrap 5 web portal
- **Episode automation** - Auto-generate all 12 season episodes
- **Data migration system** - Seamless file-to-database migration
- **Flask-Migrate integration** - Database schema management

### Planned Enhancements 🚀
- **MCP Server Integration**: Claude Desktop integration for story management
- **Vector Database**: Story continuity and overlap prevention
- **Video Enhancement**: ComfyUI integration for animated story images
- **YouTube Shorts**: Automated promotional content generation
- **PSA Segments**: Fun educational segments at episode end
- **Advanced Analytics**: Story performance and engagement metrics

## 📝 Documentation

- **`CLAUDE.md`**: Development guide for Claude Code integration
- **`claude_done/`**: Detailed implementation documentation and session notes
- **API Documentation**: Available at `/api/v1/swagger` when running
- **Character Documentation**: Individual character files in `ephergent_generator/prompts/characters/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Follow the existing code patterns and documentation standards
4. Test thoroughly with both web interface and API
5. Update relevant documentation
6. Submit a pull request with clear description

## 📄 License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.

### License Highlights
- Open-source and free to use
- Commercial use allowed
- Modification and distribution permitted
- No warranty provided

## 🆘 Support

### Getting Help
- **GitHub Issues**: [Report bugs](https://github.com/yourusername/ephergent-generator/issues) and request features
- **Documentation**:
  - Technical details in `claude_done/` directory
  - API Reference: Swagger documentation at `/api/v1/swagger`
  - Configuration guide: `.env.example`

### Contact
- **Project Maintainer**: [Your Name]
- **Email**: support@ephergent.com
- **Community**: [Discord/Slack/Forum Link]

### Professional Support
- Consulting available for custom deployments
- Training and integration services
- Enterprise support packages

---

**Welcome to The Ephergent Universe Season 03! 🚀**

*Generate compelling weekly stories with AI-powered characters, complete media production, and automated publishing for your interdimensional journalism adventures.*