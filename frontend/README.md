# Frontend Architecture Documentation

## Overview

Simple frontend to test all agent patterns

## File Structure

```
frontend/
├── index.html              # Clean HTML structure (no inline styles/scripts)
├── assets/
│   ├── css/                # Organized stylesheets
│   │   ├── main.css        # Core layout and base styles
│   │   ├── chat.css        # Chat panel styles
│   │   ├── process-panel.css  # Thought process panel styles
│   │   ├── components.css  # Stage selector, context monitor, tabs
│   │   ├── alerts.css      # Struggle alerts and multi-agent viz
│   │   └── animations.css  # Animations and responsive design
│   └── js/                 # Modular JavaScript (ES6 modules)
│       ├── config.js       # Configuration constants
│       ├── state.js        # Application state management
│       ├── utils.js        # Utility functions
│       ├── ui.js           # UI updates and monitoring
│       ├── chat.js         # Chat functionality and messaging
│       ├── stages.js       # Stage selection and switching
│       ├── checkpoints.js  # Checkpoint debugging
│       └── app.js          # Main entry point and initialization
└── components/             # Reserved for future component templates
```

## Architecture Principles

### 1. **Separation of Concerns**
- **HTML**: Semantic structure only, no inline styles or scripts
- **CSS**: Organized by feature/component in separate files
- **JavaScript**: Modular ES6 modules with clear responsibilities

### 2. **Module Organization**

#### Configuration (`config.js`)
- Centralized configuration constants
- API endpoints, limits, and settings
- Easy to modify without touching business logic

#### State Management (`state.js`)
- Single source of truth for application state
- Encapsulated state with getter/setter methods
- Session management and persistence

#### Utilities (`utils.js`)
- Reusable helper functions
- Token estimation, formatting, validation
- Stage and specialist information helpers

#### UI Management (`ui.js`)
- Context monitor updates
- Tab switching
- Thread ID display
- Stage subtitle management

#### Chat (`chat.js`)
- Message sending and receiving
- Streaming response handling
- Process item visualization
- ReWOO and Stage 4 specialized displays

#### Stages (`stages.js`)
- Stage discovery and selection
- Tools fetching and display
- Stage switching logic

#### Checkpoints (`checkpoints.js`)
- Checkpoint loading and visualization
- Time-travel debugging
- State inspection

#### Main App (`app.js`)
- Application initialization
- Event listener setup
- Backend health checks
- Module coordination

### 3. **CSS Organization**

Each CSS file focuses on a specific aspect:
- `main.css`: Core layout, container grid, base styles
- `chat.css`: Chat messages, input, send button
- `process-panel.css`: Thought process panel, process items
- `components.css`: Stage selector, context monitor, tabs, debug
- `alerts.css`: Struggle alerts, supervisor visualization
- `animations.css`: Keyframe animations, responsive breakpoints

## Usage

### Development
Simply open `index.html` in a browser (with backend running):
```bash
# In the frontend directory
open index.html

# Then run 
python3 -m http.server 8080
```

### Adding New Features

**Adding a new CSS component:**
1. Create new CSS file in `assets/css/`
2. Add `<link>` tag in `index.html` `<head>`

**Adding new JavaScript functionality:**
1. Create new module in `assets/js/`
2. Import in relevant modules (typically `app.js`)
3. Export functions that need to be globally accessible

**Modifying existing functionality:**
1. Identify the responsible module
2. Make changes in that specific file
3. Test to ensure no regressions

## Module Dependencies

```
app.js (entry point)
├── config.js (constants)
├── state.js (state management)
├── ui.js (UI updates)
│   └── state.js
├── chat.js (messaging)
│   ├── config.js
│   ├── state.js
│   ├── utils.js
│   └── ui.js
├── stages.js (stage management)
│   ├── config.js
│   ├── state.js
│   ├── utils.js
│   └── ui.js
├── checkpoints.js (debugging)
│   ├── config.js
│   ├── state.js
│   └── utils.js
└── utils.js (helpers)
    └── config.js
```
