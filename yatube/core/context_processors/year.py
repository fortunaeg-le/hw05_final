import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    now = datetime.date.today()
    return {
        'year': int(now.year)
    }
