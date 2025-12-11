# Quick Start - Uruchomienie nowego panelu admina

## 🚀 Szybkie uruchomienie

### 1. Zbierz pliki statyczne
```powershell
python manage.py collectstatic --noinput
```

### 2. Uruchom serwer
```powershell
python manage.py runserver
```

### 3. Otwórz panel admina
```
http://127.0.0.1:8000/admin/
```

## 🎨 Co zostało zmienione?

✅ **Utworzono nową strukturę:**
```
templates/admin/          # Własne szablony Django Admin
static/admin/css/        # Własne style CSS
```

✅ **Zmodyfikowano:**
- `backend/settings.py` - dodano konfigurację templates i static
- `products/admin.py` - rozszerzone pola wyświetlania
- `payments/admin.py` - dodano rejestrację modelu Payment

✅ **Utworzono:**
- `static/admin/css/custom_admin.css` - nowoczesne style
- `templates/admin/base_site.html` - własny nagłówek i logo
- `templates/admin/base.html` - główny szablon z custom CSS

## 🎨 Użyte kolory

| Kolor | Kod | Zastosowanie |
|-------|-----|--------------|
| Niebieski | #8CA9FF | Przyciski, linki |
| Jasny niebieski | #AAC4F5 | Hover, secondary |
| Beżowy | #FFF8DE | Tła |
| Kremowy | #FFF2C6 | Akcenty |

## 📝 Więcej informacji

Szczegółowa dokumentacja znajduje się w pliku:
**`ADMIN_CUSTOMIZATION_GUIDE.md`**

## 🔧 Alternatywna opcja: django-admin-interface

Jeśli wolisz gotowe rozwiązanie:

```powershell
pip install django-admin-interface
```

Dodaj do `INSTALLED_APPS` w settings.py:
```python
INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    # ... reszta
]
```

Uruchom migracje:
```powershell
python manage.py migrate
python manage.py collectstatic
```

Dostosuj kolory w GUI:
1. Panel admin → Admin Interface → Themes
2. Ustaw kolory z palety projektu
3. Zapisz

---

Gotowe! Panel admina jest nowoczesny, responsywny i gotowy do użycia! 🎉
