# HubSpot Property Comparison Tool

A web application that allows you to compare properties between two HubSpot portals with a visual diff interface.

🌐 **Live Demo**: [https://hubspot-compare-38zun.ondigitalocean.app/](https://hubspot-compare-38zun.ondigitalocean.app/)

## Features

- **Property Comparison**: Compare properties between two HubSpot portals side-by-side
- **Property-to-Property Comparison**: Compare specific properties across different object types and portals
- **Visual Diff Interface**: Git-diff style visualization with color-coded differences
- **Standard Objects**: Support for contacts, companies, deals, tickets, products, line items, and more
- **Custom Objects**: Compare custom object properties with intelligent matching system
- **Session Management**: Secure sessions with portal naming and caching
- **Filtering**: Show only differences, similarities, or properties unique to each portal
- **Search**: Find specific properties quickly
- **Validation Rules**: Compare property validation rules and constraints
- **Property Groups**: Display and compare property grouping information

## Setup Instructions

### Prerequisites

- Python 3.11+
- uv package manager (recommended) or pip
- HubSpot private app tokens for both portals you want to compare

### Local Development

1. **Clone and navigate to the project:**
   ```bash
   cd hubspot-compare
   ```

2. **Install dependencies with uv:**
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the development server:**
   ```bash
   # With uv
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   
   # Or directly
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Open your browser to:**
   ```
   http://localhost:8000
   ```

### Production Deployment

The application is currently deployed on DigitalOcean App Platform. For your own deployment:

1. **DigitalOcean App Platform** (recommended):
   - Connect your GitHub repository
   - Configure build settings to use Python with the requirements from `requirements.txt`
   - Set the run command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Other platforms** (Heroku, Railway, etc.):
   - Ensure Python 3.11+ runtime
   - Install dependencies with `pip install -r requirements.txt`
   - Run with `uvicorn main:app --host 0.0.0.0 --port $PORT`

## How to Use

### 1. Get HubSpot Private App Tokens

For each HubSpot portal you want to compare:

1. Go to your HubSpot portal → Settings → Private Apps
2. Create a new private app or use an existing one
3. Grant the following scopes:
   - `crm.objects.contacts.read`
   - `crm.objects.companies.read`
   - `crm.objects.deals.read`
   - `crm.objects.tickets.read`
   - `crm.schemas.contacts.read`
   - `crm.schemas.companies.read`
   - `crm.schemas.deals.read`
   - `crm.schemas.tickets.read`
   - `crm.schemas.custom.read` (for custom objects)
4. Copy the generated access token

### 2. Compare Properties

#### Standard Object Comparison
1. **Enter Tokens**: Paste both portal tokens and give them memorable names
2. **Select Object**: Choose from standard objects (Contacts, Companies, etc.) or custom objects
3. **Review Comparison**: View the side-by-side property comparison with highlighted differences
4. **Filter Results**: Use filters to show only differences, similarities, or portal-specific properties
5. **Search Properties**: Use the search box to find specific properties quickly

#### Property-to-Property Comparison
1. **Access Feature**: Click "⚡ Property-to-Property Comparison" from the home page
2. **Select Source Property**: Choose portal, object type, and specific property
3. **Select Target Property**: Choose portal, object type, and specific property to compare against
4. **Compare**: View detailed comparison excluding property groups (useful for cross-object comparisons)

#### Custom Object Comparison
1. **Select Custom Objects**: Choose "Custom Objects" from the object selection
2. **Match Objects**: Use the matching interface to pair custom objects between portals
3. **Compare**: Review properties for the matched custom object types

## Project Structure

```
hubspot-compare/
├── pyproject.toml              # uv configuration
├── requirements.txt            # pip requirements for deployment
├── main.py                     # FastAPI application
├── api/
│   ├── __init__.py
│   ├── hubspot_client.py       # HubSpot API client
│   ├── comparison.py           # Property comparison logic
│   └── models.py               # Pydantic data models
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css      # Application styles
│   │   └── js/
│   │       └── app.js          # Frontend JavaScript
│   └── templates/
│       ├── index.html              # Homepage
│       ├── comparison.html         # Standard comparison view
│       ├── property_to_property.html  # Property-to-property comparison
│       └── custom_object_matching.html # Custom object matching interface
└── utils/
    ├── __init__.py
    └── helpers.py              # Utility functions
```

## API Endpoints

### Core Endpoints
- `GET /` - Homepage
- `POST /validate-tokens` - Validate HubSpot tokens and create session
- `GET /objects/{session_id}` - Get available objects for both portals
- `GET /properties/{session_id}/{object_type}` - Get properties for an object type
- `GET /compare/{session_id}/{object_type}` - Standard object comparison view

### Property-to-Property Comparison
- `GET /property-to-property/{session_id}` - Property selection interface
- `GET /compare-property/{session_id}` - Compare two specific properties

### Custom Object Support
- `GET /custom-object-matching/{session_id}` - Custom object matching interface
- `GET /compare-custom/{session_id}/{portal_a_id}/{portal_b_id}` - Compare matched custom objects

### Utility Endpoints
- `POST /refresh-cache/{session_id}` - Refresh cached property data
- `GET /cache-status/{session_id}` - Check cache status

## Features in Detail

### Property Comparison Types

#### 1. Standard Object Comparison
- **Side-by-side comparison** of all properties for standard HubSpot objects
- **Detailed property information** including type, options, validation rules, and property groups
- **Option comparison** for enumeration/select fields with detailed option analysis
- **Validation rule comparison** showing constraints and requirements

#### 2. Property-to-Property Comparison
- **Cross-object comparison** - Compare properties between different object types
- **Cross-portal comparison** - Compare properties within the same portal
- **Flexible selection** - Choose any property from any available object
- **Group exclusion** - Property groups are excluded from comparison since they're expected to differ

#### 3. Custom Object Comparison
- **Intelligent matching** - Manual pairing of custom objects between portals
- **ID resolution** - Handles different custom object IDs between portals
- **Full property analysis** - Same detailed comparison as standard objects

### Visual Diff Interface
- **Color-coded differences**:
  - ✅ Green: Identical properties
  - ⚠️ Yellow: Different properties
  - ← Blue: Only in Portal A
  - → Red: Only in Portal B
- **Expandable details** showing specific field differences
- **Property groups** displayed prominently
- **Clean, readable layout** inspired by git diff tools

### Session Management & Caching
- **Secure session handling** with unique session IDs
- **Portal naming** for easy identification
- **Intelligent caching** to reduce API calls and improve performance
- **Cache refresh** capability for updated data
- **Session persistence** during browser session

### Filtering and Search
- **Toggle visibility** of different property types
- **Real-time search** through property names and labels
- **Summary statistics** showing counts of each comparison type
- **Advanced filtering** options for focused analysis

## Security Notes

- **Temporary storage**: Tokens are stored only in server memory during active sessions
- **No persistence**: No sensitive data is stored permanently
- **Session expiration**: Sessions automatically expire after 1 hour
- **HTTPS**: Production deployment uses HTTPS encryption
- **No logging**: Sensitive token data is not logged to prevent exposure

## Development

### Adding New Object Types

To add support for new HubSpot object types:

1. Add the object type to the standard objects list in `frontend/static/js/app.js`
2. Ensure your HubSpot tokens have the appropriate read scopes
3. Test the new object type with your portals

### Customizing the UI

- Modify `frontend/static/css/styles.css` for styling changes
- Update templates in `frontend/templates/` for layout changes
- Extend `frontend/static/js/app.js` for additional functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request