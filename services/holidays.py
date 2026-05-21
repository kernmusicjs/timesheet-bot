"""French national + Alsace-Moselle holidays for a given year."""

from datetime import date, timedelta


def _easter(year: int) -> date:
    """Compute Easter Sunday for a given year (Gauss algorithm)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def french_holidays(year: int, alsace_moselle: bool = True) -> dict:
    """Return {date: name} of public holidays for the year."""
    easter = _easter(year)
    days = {
        date(year, 1, 1): "Jour de l'an",
        easter + timedelta(days=1): "Lundi de Pâques",
        date(year, 5, 1): "Fête du Travail",
        date(year, 5, 8): "Victoire 1945",
        easter + timedelta(days=39): "Ascension",
        easter + timedelta(days=50): "Lundi de Pentecôte",
        date(year, 7, 14): "Fête nationale",
        date(year, 8, 15): "Assomption",
        date(year, 11, 1): "Toussaint",
        date(year, 11, 11): "Armistice 1918",
        date(year, 12, 25): "Noël",
    }
    if alsace_moselle:
        days[easter - timedelta(days=2)] = "Vendredi Saint"
        days[date(year, 12, 26)] = "Saint-Étienne"
    return days


def is_holiday(d: date, alsace_moselle: bool = True) -> str | None:
    """Return holiday name if d is a holiday, else None."""
    return french_holidays(d.year, alsace_moselle).get(d)
