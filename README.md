# HubSpot Property Comparison Tool

A web application that allows you to compare properties between two HubSpot portals with a visual diff interface.

## Features

- **Property Comparison**: Compare properties between two HubSpot portals side-by-side
- **Visual Diff Interface**: Git-diff style visualization with color-coded differences
- **Standard Objects**: Support for contacts, companies, deals, tickets, and more
- **Custom Objects**: Compare custom object properties with manual mapping
- **Filtering**: Show only differences, similarities, or properties unique to each portal
- **Search**: Find specific properties quickly
- **Export Ready**: Built for easy deployment on Vercel

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

### Deployment on Vercel

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Deploy:**
   ```bash
   vercel
   ```

3. **Follow the prompts to complete deployment**

The `vercel.json` configuration is already set up for Python deployment.

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

1. **Enter Tokens**: Paste both portal tokens on the homepage
2. **Select Object**: Choose from standard objects (Contacts, Companies, etc.) or custom objects
3. **Review Comparison**: View the side-by-side property comparison with highlighted differences
4. **Filter Results**: Use filters to show only differences, similarities, or portal-specific properties
5. **Search Properties**: Use the search box to find specific properties quickly

## Project Structure

```
hubspot-compare/
├── pyproject.toml              # uv configuration
├── requirements.txt            # pip requirements for Vercel
├── main.py                     # FastAPI application
├── vercel.json                 # Vercel deployment config
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
│       ├── index.html          # Homepage
│       └── comparison.html     # Comparison view
└── utils/
    ├── __init__.py
    └── helpers.py              # Utility functions
```

## API Endpoints

- `GET /` - Homepage
- `POST /validate-tokens` - Validate HubSpot tokens
- `GET /objects/{session_id}` - Get available objects
- `GET /properties/{session_id}/{object_type}` - Get properties for an object
- `GET /compare/{session_id}/{object_type}` - Compare properties view

## Features in Detail

### Property Comparison
- **Side-by-side comparison** of properties from two portals
- **Detailed property information** including type, options, requirements
- **Option comparison** for enumeration/select fields
- **Status indicators** for identical, different, or portal-specific properties

### Visual Diff Interface
- **Color-coded differences**:
  - ✅ Green: Identical properties
  - ⚠️ Yellow: Different properties
  - ← Blue: Only in Portal A
  - → Red: Only in Portal B
- **Expandable details** showing specific differences
- **Clean, readable layout** inspired by git diff tools

### Filtering and Search
- **Toggle visibility** of different property types
- **Real-time search** through property names
- **Summary statistics** showing counts of each comparison type

## Security Notes

- Tokens are stored temporarily in server memory during session
- No persistent storage of sensitive data
- HTTPS recommended for production deployments
- Consider implementing proper session management for production use

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