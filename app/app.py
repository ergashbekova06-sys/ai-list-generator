import streamlit as st
import openai
import pandas as pd
from fpdf import FPDF
import os

# --- Настройка API ключа ---
# Вставьте сюда свой ключ OpenAI или используйте переменную окружения
openai.api_key = os.getenv("OPENAI_API_KEY") or "вставьте_сюда_свой_ключ"

st.set_page_config(page_title="AI Генератор рабочих листов", layout="wide")
st.title("🤖 AI Генератор рабочих листов для учителей")

# --- Настройки генерации ---
st.sidebar.header("Настройки")
subject = st.sidebar.selectbox("Выберите предмет", ["Физика", "Математика", "Биология", "Химия", "История"])
grade = st.sidebar.selectbox("Класс", list(range(1, 12)))
difficulty = st.sidebar.selectbox("Уровень сложности", ["Легкий", "Средний", "Сложный"])
num_tasks = st.sidebar.slider("Количество заданий", min_value=1, max_value=20, value=5)

prompt = st.text_area("Введите тему или ключевые слова для заданий:", "")

# --- Генерация заданий ---
if st.button("Сгенерировать рабочий лист"):
    if prompt.strip() == "":
        st.warning("Пожалуйста, введите тему или ключевые слова!")
    else:
        with st.spinner("Генерируем задания..."):
            try:
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Ты помощник учителя, создающий готовые задания, тесты и упражнения."},
                        {"role": "user", "content": f"Создай {num_tasks} заданий по предмету {subject}, для {grade} класса, уровень сложности {difficulty}, по теме: {prompt}. Представь их в виде таблицы с колонками: '№', 'Задание', 'Тип' (тест/упражнение/задача)."}
                    ],
                    temperature=0.7,
                    max_tokens=1200
                )
                tasks_text = response.choices[0].message.content

                # Попробуем преобразовать в DataFrame (если ИИ вернул таблицу)
                try:
                    from io import StringIO
                    df = pd.read_csv(StringIO(tasks_text), sep="|")
                    st.dataframe(df)
                except:
                    st.text(tasks_text)
                    # Создадим DataFrame вручную для PDF
                    df = pd.DataFrame([x.strip().split('.') for x in tasks_text.split('\n') if x.strip() != ""],
                                      columns=["№", "Задание", "Тип"])

                # --- Кнопка для скачивания PDF ---
                if st.button("Скачать PDF"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.cell(0, 10, f"Рабочий лист по предмету {subject}, {grade} класс", ln=True)
                    pdf.ln(5)

                    # Добавляем задания
                    for i, row in df.iterrows():
                        pdf.multi_cell(0, 8, f"{row['№']}. {row['Задание']} ({row['Тип']})")
                        pdf.ln(1)

                    pdf_file = "worksheet.pdf"
                    pdf.output(pdf_file)
                    with open(pdf_file, "rb") as f:
                        st.download_button("Скачать PDF", f, file_name=pdf_file, mime="application/pdf")

            except Exception as e:
                st.error(f"Ошибка при генерации: {e}")

