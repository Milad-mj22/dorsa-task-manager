import jdatetime

def convert_jalali_to_gregorian(jalali_date_str):
    # فرض: فرمت ورودی '۱۴۰۴/۰۵/۱۴' و به صورت فارسی
    jalali_date_str = jalali_date_str.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789'))
    year, month, day = map(int, jalali_date_str.split('/'))
    gregorian_date = jdatetime.date(year, month, day).togregorian()
    return gregorian_date.strftime('%Y-%m-%d')
