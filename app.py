from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Инициализация базы данных
db = SQLAlchemy(app)

from models import Message


# Главная страница с сообщениями
@app.route('/admin/messages')
def admin_messages():
    messages = Message.query.all()  # Получаем все сообщения
    return render_template('admin_messages.html', messages=messages)


# Страница с деталями сообщения
@app.route('/admin/messages/<int:message_id>', methods=['GET', 'POST'])
def admin_message_details(message_id):
    message = Message.query.get_or_404(message_id)

    if request.method == 'POST':
        # Обработка отправки ответа и обновления статуса
        admin_reply = request.form.get('admin_reply')
        mark_resolved = request.form.get('mark_resolved') == 'on'

        message.admin_comment = admin_reply
        message.is_resolved = mark_resolved

        db.session.commit()  # Сохраняем изменения в базе данных

        return redirect(url_for('admin_messages'))  # Перенаправляем на список сообщений

    return render_template('message_details.html', message=message)


# Маршрут для переключения статуса сообщения (решено/нерешено)
@app.route('/admin/messages/<int:message_id>/toggle_status', methods=['POST'])
def admin_toggle_message_status(message_id):
    message = Message.query.get_or_404(message_id)
    message.is_resolved = not message.is_resolved
    db.session.commit()
    return redirect(url_for('admin_message_details', message_id=message.id))
@app.route('/')
def hello():
    return 'Hello, World!'


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)