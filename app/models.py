from app import db
import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.String(100), nullable=True)
    schedule = db.Column(db.String(100), nullable=True)
    photo_url = db.Column(db.String(300), nullable=True)

    def get_available_times(self):
        try:
            if not self.schedule:
                return []

            # Очікуємо формат: "Пн-Пт 09:00–15:00" або подібне
            parts = self.schedule.strip().split()
            if len(parts) < 2:
                return []

            time_part = parts[1]  # друга частина — час
            # замінимо будь-який тип тире на звичайне
            time_part = time_part.replace("–", "-").replace("—", "-")

            start_time_str, end_time_str = time_part.split("-")
            start_hour = int(start_time_str.strip().split(":")[0])
            end_hour = int(end_time_str.strip().split(":")[0])

            times = []
            for hour in range(start_hour, end_hour):
                times.append(f"{hour:02d}:00")
            return times

        except Exception as e:
            print(f"⚠️ get_available_times error: {e}")
            return []


    def get_working_days(self, days_ahead=14):
   

        weekdays_map = {
            "Пн": 0, "Вт": 1, "Ср": 2, "Чт": 3,
            "Пт": 4, "Сб": 5, "Нд": 6
        }

        result = []
        today = datetime.date.today()

        try:
            day_part = self.schedule.split()[0]  # Наприклад: "Пн-Пт"
            start_day, end_day = day_part.split("-")
            start_idx = weekdays_map[start_day]
            end_idx = weekdays_map[end_day]
        except Exception as e:
            # fallback, якщо щось піде не так
            start_idx = 0
            end_idx = 4  # Пн-Пт за замовчуванням

        for i in range(days_ahead):
            date = today + datetime.timedelta(days=i)
            if start_idx <= date.weekday() <= end_idx:
                result.append(date.strftime("%Y-%m-%d"))

        return result
    
    


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
