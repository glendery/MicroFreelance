import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_platform.settings')
django.setup()

from marketplace.models import User, Project, Category

def seed():
    print("Mulai seeding data simulasi profesional...")

    # 0. Buat Kategori
    categories = ['Programming', 'Design', 'Writing', 'Translation']
    cat_objs = {}
    for cat_name in categories:
        cat, _ = Category.objects.get_or_create(name=cat_name)
        cat_objs[cat_name] = cat
        print(f"Category: {cat_name}")

    # 1. Buat User Client (Pemberi Kerja)
    clients_data = [
        {'username': 'pak_bambang', 'email': 'bambang@kopi.id', 'role': 'CLIENT', 'balance': 750000},
        {'username': 'ibu_ratna', 'email': 'ratna@butik.com', 'role': 'CLIENT', 'balance': 1200000},
        {'username': 'andre_startup', 'email': 'andre@tech.id', 'role': 'CLIENT', 'balance': 2000000},
    ]

    for data in clients_data:
        user, created = User.objects.get_or_create(username=data['username'], defaults={
            'email': data['email'],
            'role': data['role'],
            'balance': data['balance']
        })
        if created:
            user.set_password('pass123')
            user.save()
            print(f"User Client created: {user.username}")

    # 2. Buat User Freelancer (Pekerja)
    freelancers_data = [
        {'username': 'rizky_design', 'email': 'rizky@gmail.com', 'role': 'FREELANCER', 'balance': 0},
        {'username': 'maya_writer', 'email': 'maya@outlook.com', 'role': 'FREELANCER', 'balance': 0},
        {'username': 'fajar_dev', 'email': 'fajar@yahoo.com', 'role': 'FREELANCER', 'balance': 0},
    ]

    for data in freelancers_data:
        user, created = User.objects.get_or_create(username=data['username'], defaults={
            'email': data['email'],
            'role': data['role'],
            'balance': data['balance']
        })
        if created:
            user.set_password('pass123')
            user.save()
            print(f"User Freelancer created: {user.username}")

    # 3. Buat Project Simulasi
    pak_bambang = User.objects.get(username='pak_bambang')
    ibu_ratna = User.objects.get(username='ibu_ratna')
    andre = User.objects.get(username='andre_startup')
    rizky = User.objects.get(username='rizky_design')

    projects_data = [
        {
            'title': 'Desain Banner Promo Warung Kopi',
            'description': 'Dibutuhkan desain banner untuk promo ramadhan ukuran 2x1 meter. Tema tradisional modern.',
            'budget': 150000,
            'client': pak_bambang,
            'category': cat_objs['Design'],
            'status': 'OPEN'
        },
        {
            'title': 'Deskripsi Produk Gamis Lebaran (50 Produk)',
            'description': 'Menulis deskripsi produk yang menarik (copywriting) untuk 50 item gamis di Tokopedia.',
            'budget': 250000,
            'client': ibu_ratna,
            'category': cat_objs['Writing'],
            'status': 'OPEN'
        },
        {
            'title': 'Testing Landing Page Startup Baru',
            'description': 'Mencoba fitur pendaftaran dan memberikan feedback tertulis mengenai UI/UX.',
            'budget': 100000,
            'client': andre,
            'category': cat_objs['Programming'],
            'status': 'OPEN'
        },
        {
            'title': 'Logo Brand Katering Sehat',
            'description': 'Membuat logo minimalis untuk brand katering diet sehat.',
            'budget': 300000,
            'client': pak_bambang,
            'category': cat_objs['Design'],
            'status': 'IN_PROGRESS',
            'freelancer': rizky
        },
    ]

    for data in projects_data:
        project, created = Project.objects.get_or_create(title=data['title'], defaults=data)
        if created:
            print(f"Project created: {project.title}")

    print("Seeding data selesai!")

if __name__ == '__main__':
    seed()
