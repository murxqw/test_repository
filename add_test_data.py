from app import create_app, db
from app.models import User, Doctor
from werkzeug.security import generate_password_hash

app = create_app()

doctors = [
    {
        "username": "dr_shevchenko",
        "name": "Олег Шевченко",
        "specialty": "Кардіолог",
        "experience": "15 років стажу",
        "schedule": "Пн-Пт 9:00–15:00",
        "photo_url": "images/32.jpg"
    },
    {
        "username": "dr_kovalenko",
        "name": "Марія Коваленко",
        "specialty": "Терапевт",
        "experience": "10 років стажу",
        "schedule": "Пн-Ср 10:00–17:00",
        "photo_url": "images/44.jpg"
    },
    {
        "username": "dr_pavlenko",
        "name": "Андрій Павленко",
        "specialty": "Офтальмолог",
        "experience": "8 років стажу",
        "schedule": "Вт-Чт 11:00–18:00",
        "photo_url": "images/45.jpg"
    },
    {
        "username": "dr_ivanenko",
        "name": "Ірина Іваненко",
        "specialty": "Гастроентеролог",
        "experience": "12 років стажу",
        "schedule": "Пн-Пт 8:30–13:30",
        "photo_url": "images/51.jpg"
    },
    {
        "username": "dr_bondarenko",
        "name": "Юрій Бондаренко",
        "specialty": "Невролог",
        "experience": "18 років стажу",
        "schedule": "Ср-Пт 13:00–19:00",
        "photo_url": "images/61.jpg"
    },
    {
        "username": "dr_petryk",
        "name": "Наталія Петрик",
        "specialty": "Дерматолог",
        "experience": "9 років стажу",
        "schedule": "Вт-Сб 10:00–16:00",
        "photo_url": "images/66.jpg"
    },
    {
        "username": "dr_khomenko",
        "name": "Богдан Хоменко",
        "specialty": "Ортопед",
        "experience": "6 років стажу",
        "schedule": "Пн-Ср 12:00–18:00",
        "photo_url": "images/70.jpg"
    }
]

with app.app_context():
    for doc in doctors:
        existing = User.query.filter_by(username=doc["username"]).first()
        if existing:
            print(f"🔁 {doc['username']} вже існує, пропущено.")
        else:
            user = User(username=doc["username"], password=generate_password_hash("test123"), role="doctor")
            db.session.add(user)
            db.session.flush()  # Для отримання user.id

            doctor = Doctor(
                id=user.id,
                name=doc["name"],
                specialty=doc["specialty"],
                experience=doc["experience"],
                schedule=doc["schedule"],
                photo_url=doc["photo_url"]
            )
            db.session.add(doctor)

    # Оновлюємо паролі для всіх існуючих лікарів у списку
    for doc in doctors:
        user = User.query.filter_by(username=doc["username"]).first()
        if user:
            user.password = generate_password_hash("test123")
            print(f"🔑 Пароль для {doc['username']} оновлено.")

    db.session.commit()
    print("Лікарів успішно додано або оновлено з хешованими паролями!")
