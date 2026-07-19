import pandas as pd

def fix_persian_text(text):
    if isinstance(text, str):
        try:
            fixed = text.encode("latin1").decode("utf-8")
            if any('\u0600' <= ch <= '\u06FF' for ch in fixed):
                return fixed
            else:
                return text
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text
    return text

def repair_excel(input_file, output_file):
    # Read the Excel file
    df = pd.read_excel(input_file)

    # Fix first name and last name columns
    df['first name'] = df['first name'].apply(fix_persian_text)
    df['last name'] = df['last name'].apply(fix_persian_text)

    # Save to a new Excel file
    df.to_excel(output_file, index=False)
    #print(f"✅ Fixed file saved to: {output_file}")




def repair_csv(input_file, output_file):
    # Read the CSV file
    df = pd.read_csv(input_file)

    # Fix first name and last name columns
    if 'first name' in df.columns:
        df['first name'] = df['first name'].apply(fix_persian_text)
    if 'last name' in df.columns:
        df['last name'] = df['last name'].apply(fix_persian_text)

    # Save to a new CSV file
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    df.to_excel(output_file, index=False)


    #print(f"✅ Fixed CSV file saved to: {output_file}")


import re
import gender_guesser.detector as gender
from persian_gender_detection import get_gender
d = gender.Detector()

def detect_gender(name):
    # تشخیص اینکه فارسیه یا نه
    if re.search(r'[\u0600-\u06FF]', name):  # حروف فارسی
        return get_gender(name)
    else:
        return d.get_gender(name)








import pandas as pd
from django.contrib.auth.models import User
from timeTracker.models import Team, Sprint, Story, Task
from decimal import Decimal
from django.shortcuts import render
from .forms import CSVUploadForm
from django.contrib.auth.decorators import login_required


@login_required
def import_tasks_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            team_name = request.POST['team_name']
            sprint_name = request.POST['sprint_name']
            csv_file = request.FILES['file']

            try:
                df = pd.read_csv(csv_file)
            except Exception as e:
                return render(request, 'import_tasks.html', {
                    'form': form,
                    'error': 'Error reading CSV file: ' + str(e),
                })

            # Get or create Team and Sprint
            team, _ = Team.objects.get_or_create(name=team_name)
            sprint, _ = Sprint.objects.get_or_create(name=sprint_name)

            current_story = None
            created_stories = 0
            created_tasks = 0

            for _, row in df.iterrows():
                title = str(row.get('عنوان داستان / تسک', '')).strip()
                try:
                    priority = int(row.get('اولویت'))
                except:
                    priority = 0
                    
                estimate_raw = str(row.get('تخمین', '')).strip()
                assigned_name = str(row.get('مجری', '')).strip()
                status = str(row.get('وضعیت', '')).strip().lower()
                description = str(row.get('توضیحات', '')).strip()

                # If تخمین is empty, this is a Story
                if not estimate_raw or estimate_raw == 'nan':
                    if title:
                        current_story = Story.objects.create(
                            title=title,
                            description=description,
                            team=team,
                            sprint=sprint,
                            priority = priority
                        )
                        created_stories += 1
                    continue

                if not current_story:
                    continue  # Skip task without a parent story

                try:
                    goal_time = Decimal(estimate_raw)
                except:
                    continue

                user = User.objects.filter(last_name__icontains=assigned_name).first()

                Task.objects.create(
                    title=title,
                    description=description,
                    story=current_story,
                    priority = current_story.priority,
                    goal_time=goal_time,
                    assigned_to=user,
                    status=status if status in ['todo', 'doing', 'done'] else 'todo',
                )
                created_tasks += 1

            return render(request, 'import_result.html', {
                'created_stories': created_stories,
                'created_tasks': created_tasks,
                'team': team,
                'sprint': sprint,
            })
    else:
        form = CSVUploadForm()
        teams = Team.objects.all()
        sprints = Sprint.objects.all()

    return render(request, 'import_tasks.html', {'form': form,'sprints':sprints,'teams':teams})
