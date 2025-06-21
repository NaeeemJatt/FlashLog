from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from .logai_handler import process_log_file

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def index():
    results = None
    csv_path = None
    kibana_url = None

    if request.method == 'POST':
        parser = request.form.get("parser", "drain")
        model = request.form.get("model", "isolation_forest")
        user_index = request.form.get("index_name", "").strip()
        index_name = user_index if user_index else f"logai-{datetime.utcnow().strftime('%Y-%m-%d')}"

        file = request.files.get('logfile')
        if not file:
            flash('No file uploaded.')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)

        try:
            result_data, csv_path = process_log_file(filepath, parser, model, index_name)
        except KeyError as e:
            flash(str(e))
            return redirect(request.url)

        num_logs = len(result_data)
        num_anomalies = result_data["is_anomaly"].sum()
        flash(f"✅ {num_logs} log entries processed. {num_anomalies} anomalies detected. Sent to index: {index_name}")

        if "timestamp" not in result_data.columns or result_data["timestamp"].isnull().all():
            flash("⚠️ Timestamp column missing in file — using system time instead.")

        results = result_data.to_dict(orient='records')
        kibana_url = f"http://localhost:5601/app/discover#/?_a=(index:'{index_name}',columns:!(_source))"

    return render_template('index.html', results=results, csv_path=csv_path, kibana_url=kibana_url)
