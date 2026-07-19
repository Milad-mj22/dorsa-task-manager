from django.shortcuts import render

# Create your views here.
# views.py
import os
import sqlite3
from django.shortcuts import render, redirect
from django.conf import settings
from .forms import DBUploadForm
from .models import Sale
from persiantools.jdatetime import JalaliDate


def upload_db(request):
    if request.method == "POST":
        form = DBUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data["file"]
            temp_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
            with open(temp_path, "wb+") as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)

            # Connect to uploaded DB
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT factnum, dat, total, kname, tel, adress FROM facts")  # adjust table name
                rows = cursor.fetchall()

                # Import data
                for row in rows:


                    jalali_str = row[1]  # example: "03/10/27"

                    # Clean and parse Jalali date (assuming format: YY/MM/DD or YYYY/MM/DD)
                    try:
                        parts = jalali_str.replace("“", "").replace("”", "").split("/")
                        if len(parts[0]) == 2:
                            # If year is short like 03 → convert to 1403
                            year = int(parts[0]) + 1400
                        else:
                            year = int(parts[0])
                        month = int(parts[1])
                        day = int(parts[2])

                        gregorian_date = JalaliDate(year, month, day).to_gregorian()
                    except Exception as e:
                        #print(f"⚠️ Error converting date {jalali_str}: {e}")
                        continue  # skip bad records








                    Sale.objects.get_or_create(
                        factnum=row[0],
                        defaults={
                            'dat': gregorian_date,
                            'total': row[2],
                            'kname': row[3],
                            'tel': row[4],
                            'address': row[5],
                        }
                    )
                conn.close()
                os.remove(temp_path)
                return render(request, "UploadDB/upload_success.html", {"count": len(rows)})

            except Exception as e:
                conn.close()
                return render(request, "UploadDB/upload_error.html", {"error": str(e)})

    else:
        form = DBUploadForm()

    return render(request, "UploadDB/upload_db.html", {"form": form})



from django.db.models import Sum
from .models import Sale
from django.db.models import Sum
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import Sale

def dashboard(request):
    top_customers = (
        Sale.objects.values('kname' , 'tel')
        .annotate(total_spent=Sum('total'))
        .order_by('-total_spent')[:10]
    )

    daily_qs = (
        Sale.objects.values('dat')
        .annotate(total_day=Sum('total'))
        .order_by('dat')
    )

    # serialize daily_sales to JSON-friendly format (date -> ISO string)
    daily_sales_list = [
        {'dat': d['dat'].isoformat() if hasattr(d['dat'], 'isoformat') else str(d['dat']),
         'total_day': float(d['total_day'] or 0)}
        for d in daily_qs
    ]

    summary = Sale.objects.aggregate(
        total_revenue=Sum('total'),
    )

    context = {
        'top_customers': top_customers,
        'daily_sales': daily_qs,
        'daily_sales_json': json.dumps(daily_sales_list, cls=DjangoJSONEncoder),
        'total_revenue': summary['total_revenue'] or 0,
        'days_count': daily_qs.count(),
        'customers_count': Sale.objects.values('kname').distinct().count(),
    }

    return render(request, 'factors_data_dashboard.html', context)
