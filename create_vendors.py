"""
Script to create sample vendor companies in the database.
Run with: python create_vendors.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from users.models import VendorCompany

def create_sample_vendors():
    """Create 5 sample vendor companies."""
    
    vendors = [
        {
            'name': 'Wydawnictwo Literackie',
            'access_code': 'literackie2024',
            'description': 'Renomowane wydawnictwo specjalizujące się w literaturze pięknej, poezji i klasyce światowej.',
        },
        {
            'name': 'Wydawnictwo Naukowe PWN',
            'access_code': 'pwn2024',
            'description': 'Wiodące wydawnictwo naukowe publikujące encyklopedie, słowniki i podręczniki akademickie.',
        },
        {
            'name': 'Znak Emotikon',
            'access_code': 'znak2024',
            'description': 'Wydawnictwo młodzieżowe oferujące bestsellery fantasy, sci-fi i literaturę YA.',
        },
        {
            'name': 'Helion SA',
            'access_code': 'helion2024',
            'description': 'Największe wydawnictwo komputerowe w Polsce, specjalizujące się w książkach IT i e-bookach technicznych.',
        },
        {
            'name': 'Nasza Księgarnia',
            'access_code': 'nasza2024',
            'description': 'Tradycyjne wydawnictwo dziecięce i młodzieżowe z bogatą historią i szeroką ofertą lektur szkolnych.',
        },
    ]
    
    created_count = 0
    
    for vendor_data in vendors:
        vendor, created = VendorCompany.objects.get_or_create(
            name=vendor_data['name'],
            defaults={
                'access_code': vendor_data['access_code'],
                'description': vendor_data['description'],
                'is_active': True,
            }
        )
        
        if created:
            created_count += 1
            print(f"✓ Utworzono: {vendor.name}")
            print(f"  Kod dostępu: {vendor_data['access_code']}")
        else:
            print(f"○ Już istnieje: {vendor.name}")
    
    print(f"\nPodsumowanie: Utworzono {created_count} nowych dostawców")
    print(f"Łącznie w bazie: {VendorCompany.objects.count()} dostawców")

if __name__ == '__main__':
    print("Tworzenie przykładowych dostawców...\n")
    create_sample_vendors()
    print("\n✓ Zakończono!")
