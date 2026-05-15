from datasette import hookimpl
from markupsafe import Markup

@hookimpl
def render_cell(value, column, table, database, datasette):
    # Check for your specific column name
    if column == "gbifID" and value:
        url = f"https://gbif.org/occurrence/{value}"
        return Markup(f'<a href="{url}">{value}</a>')