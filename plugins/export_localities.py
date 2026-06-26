from datasette import hookimpl
from datasette.utils.asgi import Response
import csv
import io

@hookimpl
def register_routes():
    print("Registering /geonomia/export-localities route")
    return [
        ("/geonomia/export-localities", export_localities),
    ]

async def export_localities(request, datasette):
    print("Exporting localities for cluster_id:", request.args.get("cluster_id"))
    # 1. Get the cluster_id from the URL query parameters
    cluster_id = request.args.get("cluster_id")
    
    # 2. Query the database
    db = datasette.get_database() # Defaults to the first attached database
    results = await db.execute(
        "SELECT gbifid, eventdate, recordedby, recordedby_first_familyname, recordnumber, recordnumber_mainnumber, locality, decimallatitude, decimallongitude, catalognumber, scientificname FROM occ WHERE cluster_stage1_id = ?", 
        [cluster_id]
    )
    
    # 3. Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(results.columns)  # Header row
    writer.writerows(results.rows)    # Data rows
    
    # 4. Return as a downloadable file
    return Response(
        output.getvalue(),
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="locality_{cluster_id}.csv"'}
    )