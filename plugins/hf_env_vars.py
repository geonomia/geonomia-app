import os
from datasette import hookimpl

@hookimpl
def extra_template_vars(template, database, table, view_name, request, datasette):
    return {
        "SPACE_HOST": os.environ.get("SPACE_HOST", "localhost"),
        # Add as many as you need here
    }