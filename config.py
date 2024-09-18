import os

# Azure DevOps configuration
AZURE_DEVOPS_ORG = os.environ.get('AZURE_DEVOPS_ORG', 'placeholder_organization')
AZURE_DEVOPS_PROJECT = os.environ.get('AZURE_DEVOPS_PROJECT', 'placeholder_project')
AZURE_DEVOPS_PAT = os.environ.get('AZURE_DEVOPS_PAT', 'placeholder_pat')

# Database configuration
PGHOST = os.environ.get('PGHOST', 'localhost')
PGPORT = os.environ.get('PGPORT', '5432')
PGDATABASE = os.environ.get('PGDATABASE', 'placeholder_db')
PGUSER = os.environ.get('PGUSER', 'placeholder_user')
PGPASSWORD = os.environ.get('PGPASSWORD', 'placeholder_password')
