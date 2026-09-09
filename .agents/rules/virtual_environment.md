# Virtual Environment Rule

For all Django operations, Python script execution, migrations, package installations, and running commands in this project, ALWAYS use the `ndtenv` virtual environment.

## Environment Specifications
- **Virtual Environment Name**: `ndtenv`
- **Virtual Environment Path**: `/Users/pramodgopinath/Desktop/Projects/NDT_Demo/ndtenv`
- **Activation Command**: `source /Users/pramodgopinath/Desktop/Projects/NDT_Demo/ndtenv/bin/activate` (or `source ../ndtenv/bin/activate` when in `ndt_demo`)
- **Python Binary**: `/Users/pramodgopinath/Desktop/Projects/NDT_Demo/ndtenv/bin/python`

## Execution Guidelines
1. Prepend commands with `source ../ndtenv/bin/activate && ...` or execute directly using `/Users/pramodgopinath/Desktop/Projects/NDT_Demo/ndtenv/bin/python manage.py ...`.
2. Do not use the system Python (`/usr/bin/python3`) or global conda base environment for running Django or installing project dependencies.
