# AGENTS.md

## Project Overview
Streamlit-based SQL Server dashboard for time tracking analysis with Entra ID authentication, TEST mode support, and sprint-based forecasting.

## Commands
- **Test Mode**: `TEST_MODE=true streamlit run app.py` (Quick demo with dummy data)
- **Dev**: `streamlit run app.py` (Local development)
- **Docker Test**: `docker-compose -f docker-compose.test.yml up -d` (Test environment)
- **Docker Simple**: `docker-compose -f docker-compose.simple.yml up -d` (Simplified container)
- **Docker Build**: `docker build -t streamlit-dashboard .`
- **Docker Run**: `docker-compose up -d` (Production)
- **Health Check**: `curl http://localhost:8501/_stcore/health`
- **Cache Clear**: Use admin tools in sidebar or `cache_manager.clear_cache()`

## Architecture
- **Frontend**: Streamlit (Python 3.11+) 
- **Database**: SQL Server with pyodbc connector (ZV table)
- **Auth**: Microsoft Entra ID via msal-python (with local fallback)
- **Container**: Docker with python:3.11-slim
- **Cache**: Filesystem-based target hours storage
- **Export**: Excel via openpyxl with formatting
- **TEST Mode**: Mock database with JSON dummy data
- **Forecasting**: Sprint-based (4 sprints, weighted) with 3 scenarios
- **Visualization**: Plotly for interactive charts and burn-down analysis

## Code Style Guidelines
- Use type hints for all function parameters and return values
- Follow PEP 8 naming conventions (snake_case for functions, PascalCase for classes)
- Use `@st.cache_data` for database queries and expensive operations
- Handle exceptions gracefully with user-friendly error messages
- Use docstrings for all classes and public methods
- Prefer composition over inheritance for component design
- Keep database queries in `config/database.py` with prepared statements
- Store configuration in JSON files, secrets in environment variables
- Make external dependencies (pyodbc, msal) optional with fallback modes
- Support both TEST_MODE and production environments

## Notes
- Target hours are persisted in filesystem cache (JSON files per project/activity)  
- User permissions are configured in `config/users.json`
- Health checks monitor database, auth service, filesystem, and configuration
- Dashboard shows project summary (Soll vs. Ist) and detailed activity breakdown
- Supports flexible hours source selection (Zeit vs. FaktStd columns)
- All features work in TEST_MODE with dummy data for immediate testing
- Forecast overrides stored in `cache/forecast_{project}_{activity}.json`
- Sprint-based forecasting uses weighted 4-sprint analysis (40%, 30%, 20%, 10%)
- Dummy data covers last 8 weeks (4 sprints) with realistic velocity variations
