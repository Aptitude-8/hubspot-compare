# HubSpot Comparison Tool - Claude Code Prompt

## Project Overview
Build a Python-based HubSpot comparison tool that allows users to compare properties across different HubSpot portals with a visual diff interface. The tool should be deployable on Vercel with FastAPI backend and a clean frontend interface.

## Technical Stack
- **Backend**: FastAPI
- **Frontend**: HTML/CSS/JavaScript (or Django templates if preferred)
- **Package Manager**: uv
- **Deployment**: Vercel
- **Python Version**: 3.11+

## Core Requirements

### 1. Authentication & Setup
- Accept two HubSpot private app tokens (Portal A and Portal B)
- Validate tokens and establish connections to both portals
- Store tokens securely during session (no persistence required initially)

### 2. Standard Object Comparison
**Priority Objects to Support:**
- Contacts
- Companies  
- Deals
- Tickets
- Custom Objects (with manual mapping)

**Functionality:**
- Fetch all properties for selected object type from both portals
- Compare properties side-by-side in a git-diff style interface
- Highlight similarities and differences
- Show property details (type, options, required status, etc.)

### 3. Custom Object Handling
- List all custom objects from both portals
- Allow user to manually map custom objects between portals (since IDs differ)
- Save mappings for the current session
- Apply same property comparison logic as standard objects

### 4. Individual Property Comparison
- Select specific properties from each portal (can be cross-object)
- Compare property configurations in detail
- Special handling for picklists/enumerations to compare options
- Support comparing properties across different object types

### 5. User Interface Requirements
- **Split-pane layout**: Portal A on left, Portal B on right
- **Diff visualization**: 
  - Green highlighting for additions
  - Red highlighting for removals
  - Yellow highlighting for modifications
  - Clean indicators for identical properties
- **Navigation**: Easy switching between object types and properties
- **Filtering**: Ability to show only differences or only similarities
- **Export**: Option to export comparison results

## API Integration
The tool will use HubSpot's Properties API endpoints:
- [HubSpot API Docs Properties](https://developers.hubspot.com/docs/api-reference/crm-properties-v3/guide)
- [HubSpot API Docs Read All Properties](https://developers.hubspot.com/docs/api-reference/crm-properties-v3/core/get-crm-v3-properties-objectType)
- [HubSpot API Docs Schemas](https://developers.hubspot.com/docs/api-reference/crm-schemas-v3/core/get-crm-object-schemas-v3-schemas)

**Standard Objects:**
- `GET /crm/v3/properties/{objectType}` (contacts, companies, deals, tickets)

**Custom Objects:**  
- `GET /crm/v3/schemas` (list custom objects)
- `GET /crm/v3/properties/{objectType}` (custom object properties)

**Authentication:**
- Use Bearer token authentication with private app tokens
- Handle rate limiting and API errors gracefully

## Project Structure
```
hubspot-comparison-tool/
├── pyproject.toml              # uv configuration
├── main.py                     # FastAPI application
├── api/
│   ├── __init__.py
│   ├── hubspot_client.py       # HubSpot API client
│   ├── comparison.py           # Comparison logic
│   └── models.py               # Pydantic models
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css      # Diff styling
│   │   └── js/
│   │       └── app.js          # Frontend logic
│   └── templates/
│       ├── index.html          # Main interface
│       └── comparison.html     # Diff view
├── utils/
│   ├── __init__.py
│   └── helpers.py              # Utility functions
└── vercel.json                 # Vercel deployment config
```

## Implementation Steps

### Phase 1: Core Backend
1. Set up FastAPI application with uv
2. Create HubSpot client class with token management
3. Implement property fetching for standard objects
4. Basic API endpoints for property comparison

### Phase 2: Frontend Interface
1. Create clean, responsive UI with split-pane layout
2. Implement token input and validation
3. Object selection interface
4. Basic property listing and comparison view

### Phase 3: Diff Visualization
1. Implement git-diff style comparison display
2. Add highlighting for differences and similarities
3. Create filtering and search functionality
4. Add export capabilities

### Phase 4: Custom Objects
1. Add custom object discovery and listing
2. Implement manual object mapping interface
3. Extend comparison logic to handle custom objects
4. Session-based mapping storage

### Phase 5: Advanced Features
1. Cross-object property comparison
2. Detailed property analysis (picklist options, validation rules)
3. Performance optimizations and caching
4. Enhanced error handling and user feedback

## Key Technical Considerations

### HubSpot API Specifics
- Handle pagination for portals with many properties
- Respect rate limits (100 requests per 10 seconds for most endpoints)
- Parse property metadata correctly (types, options, groups)
- Handle different property configurations between portals

### Deployment on Vercel
- Use Vercel's Python runtime
- Configure proper build commands for uv
- Handle static file serving
- Environment variable management for any secrets

### Performance & UX
- Implement loading states during API calls
- Cache property data during session
- Progressive loading for large property sets
- Responsive design for different screen sizes

## Success Criteria
- Successfully compare standard object properties between any two HubSpot portals
- Clear visual indication of property differences and similarities
- Intuitive interface for custom object mapping
- Cross-object property comparison functionality
- Deployable on Vercel with reliable performance
- Clean, maintainable codebase using modern Python practices

## Getting Started
Please create the initial project structure with uv configuration, basic FastAPI setup, and a simple frontend interface. Start with the HubSpot client implementation and basic property fetching for the contacts object as a proof of concept.

Include comprehensive error handling, logging, and clear documentation throughout the development process.