from django.shortcuts import render, redirect
from .forms import ManualInputForm, FileUploadForm
from model.predict import predict_single, feature_names
import pandas as pd
import os
from datetime import datetime
import json
from django.http import FileResponse, HttpResponseRedirect
from django.urls import reverse
from .models import RealTimeLog
from django.views.decorators.http import require_POST



def home(request):
    return render(request, 'core/home.html')

def manual_predict_view(request):
    prediction = None

    if request.method == 'POST':
        form = ManualInputForm(request.POST)
        if form.is_valid():
            input_data = form.cleaned_data
            full_input = {feature: input_data.get(feature, 0) or 0 for feature in feature_names}
            prediction = predict_single(full_input)
    else:
        form = ManualInputForm()

    return render(request, 'core/manual_predict.html', {
        'form': form,
        'basic_fields': form.get_basic_fields(),
        'advanced_fields': form.get_advanced_fields(),
        'prediction': prediction
    })


def batch_predict_view(request):
    prediction_table = None
    message = ""
    
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['csv_file']
            try:
                df = pd.read_csv(file)

                # Load model
                from model.predict import model, feature_names

                # Handle infinite, missing
                df.replace([float('inf'), float('-inf')], 0, inplace=True)
                df.fillna(0, inplace=True)

                # Match required columns
                missing_cols = [col for col in feature_names if col not in df.columns]
                if missing_cols:
                    message = f"Missing columns: {', '.join(missing_cols)}"
                else:
                    # Predict
                    X = df[feature_names]
                    predictions = model.predict(X)
                    df['Prediction'] = predictions
                    prediction_table = df.to_dict('records')

                    # Save to logs
                    os.makedirs("logs", exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    log_file = f"logs/batch_log_{timestamp}.csv"
                    df.to_csv(log_file, index=False)
                    message = f"✅ Batch prediction done. Log saved to {log_file}"

            except Exception as e:
                message = f"Error: {str(e)}"
    else:
        form = FileUploadForm()

    return render(request, 'core/batch_predict.html', {
        'form': form,
        'prediction_table': prediction_table,
        'message': message
    })

def analytics_dashboard(request):
    import os
    import pandas as pd
    import json
    from .models import RealTimeLog

    # === Batch Logs ===
    batch_dir = "logs"
    batch_files = [os.path.join(batch_dir, f) for f in os.listdir(batch_dir) if f.endswith('.csv')]
    batch_pie_labels, batch_pie_values = [], []

    if batch_files:
        batch_df_list = [pd.read_csv(f) for f in batch_files]
        batch_df = pd.concat(batch_df_list, ignore_index=True)
        if 'Prediction' in batch_df.columns:
            batch_counts = batch_df['Prediction'].value_counts()
            batch_pie_labels = list(batch_counts.index)
            batch_pie_values = [int(val) for val in batch_counts.values]

    # === Real-Time Logs ===
    realtime_logs = RealTimeLog.objects.all()
    realtime_df = pd.DataFrame(list(realtime_logs.values()))
    realtime_pie_labels, realtime_pie_values = [], []

    if not realtime_df.empty and 'prediction' in realtime_df.columns:
        realtime_counts = realtime_df['prediction'].value_counts()
        realtime_pie_labels = list(realtime_counts.index)
        realtime_pie_values = [int(val) for val in realtime_counts.values]

    return render(request, 'core/combined_analytics.html', {
        # Batch
        'batch_labels': json.dumps(batch_pie_labels),
        'batch_values': json.dumps(batch_pie_values),
        # Real-Time
        'realtime_labels': json.dumps(realtime_pie_labels),
        'realtime_values': json.dumps(realtime_pie_values),
    })


def view_logs(request):
    logs_dir = 'logs'
    log_files = [f for f in os.listdir(logs_dir) if f.endswith('.csv')]
    all_logs = []

    for file in log_files:
        path = os.path.join(logs_dir, file)
        df = pd.read_csv(path)
        preview = df.head(5).to_dict(orient='records')  # Just showing top rows
        all_logs.append({
            'filename': file,
            'preview': preview,
            'columns': df.columns.tolist(),
            'total_rows': len(df)
        })

    return render(request, 'core/view_logs.html', {'logs': all_logs})


def delete_log(request, filename):
    logs_dir = 'logs'
    file_path = os.path.join(logs_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return HttpResponseRedirect(reverse('view_logs'))


def download_log(request, filename):
    logs_dir = 'logs'
    file_path = os.path.join(logs_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    return HttpResponseRedirect(reverse('view_logs'))

def realtime_logs(request):
    logs = RealTimeLog.objects.order_by('-timestamp')[:100]  # latest 100 entries
    return render(request, 'core/realtime_logs.html', {'logs': logs})

@require_POST
def delete_all_realtime_logs(request):
    RealTimeLog.objects.all().delete()
    return redirect('realtime_logs')

def realtime_analytics_dashboard(request):
    from .models import RealTimeLog
    from django.db.models import Count

    # Count how many times each prediction occurred
    prediction_counts = RealTimeLog.objects.values('prediction').annotate(count=Count('prediction'))

    labels = [entry['prediction'] for entry in prediction_counts]
    values = [entry['count'] for entry in prediction_counts]

    return render(request, 'core/realtime_analytics.html', {
        'pie_labels': json.dumps(labels),
        'pie_values': json.dumps(values),
        'bar_labels': json.dumps(labels),
        'bar_values': json.dumps(values),
    })

def batch_analytics_dashboard(request):
    logs_dir = "logs"
    all_files = [os.path.join(logs_dir, f) for f in os.listdir(logs_dir) if f.startswith('batch_log_') and f.endswith('.csv')]

    if not all_files:
        return render(request, 'core/batch_analytics.html', {'error': "No batch logs found."})

    df_list = [pd.read_csv(f) for f in all_files]
    full_df = pd.concat(df_list, ignore_index=True)

    if 'Prediction' not in full_df.columns:
        return render(request, 'core/batch_analytics.html', {'error': "No 'Prediction' column in batch logs."})

    prediction_counts = full_df['Prediction'].value_counts()
    
    pie_labels = list(prediction_counts.index)
    pie_values = [int(val) for val in prediction_counts.values]

    return render(request, 'core/batch_analytics.html', {
        'pie_labels': json.dumps(pie_labels),
        'pie_values': json.dumps(pie_values),
        'bar_labels': json.dumps(pie_labels),
        'bar_values': json.dumps(pie_values),
    })



