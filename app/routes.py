from flask import render_template
from flask import current_app as app
from flask import request, redirect, url_for, session, flash
from app import db
from app.models import User  # <-- цей імпорт обов'язковий!
from app.models import Doctor
from app.models import Appointment
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash


def get_free_times_for_date(doctor, date):
        all_times = doctor.get_available_times()

        # отримати вже зайняті слоти на цю дату
        taken = Appointment.query.filter_by(doctor_id=doctor.id, date=date).with_entities(Appointment.time).all()
        taken_times = {t[0] for t in taken}

        # повертаємо тільки вільні
        return [time for time in all_times if time not in taken_times]


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'admin':
                return redirect(url_for('admin_panel'))
            elif user.role == 'doctor':
                return redirect(url_for('doctor_panel'))
            else:
                return redirect(url_for('dashboard'))

        flash('Невірний логін або пароль')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = 'patient'  # автоматично призначаємо роль пацієнта

        hashed_password = generate_password_hash(password)

        user = User(username=username, password=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        session['role'] = user.role

        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Доступ лише для адміністратора")
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        specialty = request.form['specialty']

        # Додаємо User
        user = User(username=username, password=password, role='doctor')
        db.session.add(user)
        db.session.flush()  # отримуємо user.id до коміту

        # Додаємо Doctor
        doctor = Doctor(id=user.id, name=name, specialty=specialty)
        db.session.add(doctor)
        db.session.commit()
        flash("Лікаря додано успішно")

    doctors = Doctor.query.all()
    return render_template('admin_panel.html', doctors=doctors)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'patient':
        flash("Будь ласка, увійдіть в систему.")
        return redirect(url_for('login'))
    
    specialty_query = request.args.get('specialty', '').strip().lower()

    all_doctors = Doctor.query.all()

    if len(specialty_query) >= 2:
        doctors = [
            doc for doc in all_doctors
            if specialty_query in doc.specialty.lower()
        ]
    else:
        doctors = all_doctors

    return render_template('dashboard.html', doctors=doctors, search_term=specialty_query)



from datetime import datetime


@app.route('/doctor-panel')
def doctor_panel():
    if 'user_id' not in session or session.get('role') != 'doctor':
        flash("Будь ласка, увійдіть як лікар.")
        return redirect(url_for('login'))

    appointments_raw = (
        Appointment.query
        .filter_by(doctor_id=session['user_id'])
        .order_by(Appointment.date, Appointment.time)
        .all()
    )

    now = datetime.now()
    appointments = []

    for appt in appointments_raw:
        try:
            appt_date = datetime.strptime(str(appt.date), "%Y-%m-%d").date()
        except ValueError:
            appt_date = appt.date  # Якщо вже date

        appt_time = datetime.strptime(appt.time, "%H:%M").time()
        appt_datetime = datetime.combine(appt_date, appt_time)

        status = "past" if appt_datetime < now else "upcoming"
        appointments.append({
            "patient_id": appt.patient_id,
            "date": appt.date,
            "time": appt.time,
            "status": status
        })

    return render_template("doctor_panel.html", appointments=appointments)



@app.route('/make_appointment/<int:doctor_id>', methods=['GET', 'POST'])
def make_appointment(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    available_dates = doctor.get_working_days()

    if not available_dates:
        flash("⛔ Лікар не приймає найближчі два тижні.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        selected_date = request.form.get('appointment_date')
        selected_time = request.form.get('appointment_time')

        if not selected_date or not selected_time:
            flash("⚠️ Ви не вибрали дату або час!")
            return redirect(url_for('make_appointment', doctor_id=doctor.id))

        existing = Appointment.query.filter_by(
            doctor_id=doctor.id,
            date=selected_date,
            time=selected_time
        ).first()

        if existing:
            flash("⛔ Обраний час вже зайнятий. Оберіть інший.")
            return redirect(url_for('make_appointment', doctor_id=doctor.id))

        appointment = Appointment(
            patient_id=session['user_id'],
            doctor_id=doctor.id,
            date=selected_date,
            time=selected_time
        )
        db.session.add(appointment)
        db.session.commit()

        flash("✅ Ви успішно записались до лікаря!")
        return redirect(url_for('dashboard'))

    selected_date = available_dates[0]
    available_times = get_free_times_for_date(doctor, selected_date)

    return render_template(
        'make_appointment.html',
        doctor=doctor,
        available_dates=available_dates,
        available_times=available_times,
        selected_date=selected_date
    )

from datetime import datetime
import calendar

@app.route('/patient_dashboard', methods=['GET', 'POST'])
def patient_dashboard():
    if 'user_id' not in session or session.get('role') != 'patient':
        flash("Будь ласка, увійдіть в систему.")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    # Оновлення профілю
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.phone = request.form.get('phone')
        user.email = request.form.get('email')

        db.session.commit()
        flash("Профіль успішно оновлено.")
        return redirect(url_for('patient_dashboard'))

    appointments = Appointment.query.filter_by(patient_id=session['user_id']).all()
    appointments = sorted(appointments, key=lambda a: (a.date, a.time))

    total_appointments = len(appointments)

    # Найближчий запис
    next_appointment = None
    today = datetime.today().strftime('%Y-%m-%d')
    now_time = datetime.today().strftime('%H:%M')

    for appointment in appointments:
        if appointment.date > today or (appointment.date == today and appointment.time >= now_time):
            next_appointment = appointment
            break

    if not next_appointment and appointments:
        next_appointment = appointments[0]

    next_appointment_date = next_appointment.date if next_appointment else None
    next_appointment_time = next_appointment.time if next_appointment else None

    # Базовий місяць для календаря
    if appointments:
        base_date = datetime.strptime(appointments[0].date, '%Y-%m-%d')
    else:
        base_date = datetime.today()

    year = base_date.year
    month = base_date.month

    month_names_uk = {
        1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень",
        5: "Травень", 6: "Червень", 7: "Липень", 8: "Серпень",
        9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень"
    }

    current_month = f"{month_names_uk[month]} {year}"

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    calendar_days = []
    for week in month_days:
        for day in week:
            calendar_days.append("" if day == 0 else str(day))

    busy_days = []
    for appointment in appointments:
        appt_date = datetime.strptime(appointment.date, '%Y-%m-%d')
        if appt_date.year == year and appt_date.month == month:
            day_str = str(appt_date.day)
            if day_str not in busy_days:
                busy_days.append(day_str)

    selected_day = request.args.get('day')
    if not selected_day:
        selected_day = busy_days[0] if busy_days else '1'

    selected_date_appointments = []
    for appointment in appointments:
        appt_date = datetime.strptime(appointment.date, '%Y-%m-%d')
        if (
            appt_date.year == year and
            appt_date.month == month and
            str(appt_date.day) == str(selected_day)
        ):
            doctor = Doctor.query.get(appointment.doctor_id)
            doctor_name = doctor.name if doctor else 'Лікар'

            selected_date_appointments.append({
                'time': appointment.time,
                'doctor': doctor_name
            })

    selected_date = f"{selected_day} {month_names_uk[month].lower()}"
    selected_date_count = f"{len(selected_date_appointments)} запис(ів) заплановано"

    # Для блоку "Мої записи"
    appointments_display = []
    for appointment in appointments[:4]:
        doctor = Doctor.query.get(appointment.doctor_id)
        appointments_display.append({
            'id': appointment.id,
            'date': appointment.date,
            'time': appointment.time,
            'doctor_name': doctor.name if doctor else 'Лікар',
            'specialty': doctor.specialty if doctor else 'Прийом'
        })

    return render_template(
        'patient_dashboard.html',
        user=user,
        appointments=appointments_display,
        total_appointments=total_appointments,
        next_appointment_date=next_appointment_date,
        next_appointment_time=next_appointment_time,
        predicted_delay='5 хв',
        recommended_slot='15:20',
        best_day='Четвер',
        recommended_doctor='Терапевт',
        current_month=current_month,
        calendar_days=calendar_days,
        busy_days=busy_days,
        selected_day=str(selected_day),
        selected_date=selected_date,
        selected_date_count=selected_date_count,
        selected_date_appointments=selected_date_appointments
    )


@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    if session.get('user_id') != appointment.patient_id:
        flash("У вас немає доступу до цього запису.")
        return redirect(url_for('patient_dashboard'))

    db.session.delete(appointment)
    db.session.commit()
    flash("Запис успішно скасовано.")
    return redirect(url_for('patient_dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


