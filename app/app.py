import streamlit as st
import openai
import pandas as pd
from fpdf import FPDF
import os
from io import BytesIO

# --- Настройка API ключа ---
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

                # Попробуем создать DataFrame
                try:
                    from io import StringIO
                    df = pd.read_csv(StringIO(tasks_text), sep="|")
                except:
                    # Если ИИ вернул обычный текст, разделяем по строкам
                    lines = [line.strip() for line in tasks_text.split("\n") if line.strip() != ""]
                    data = []
                    for idx, line in enumerate(lines, 1):
                        data.append([idx, line, "Задача"])
                    df = pd.DataFrame(data, columns=["№", "Задание", "Тип"])

                st.dataframe(df)

                # --- Кнопка для скачивания PDF ---
                pdf = FPDF()
                pdf.add_page()
                pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
                pdf.set_font("DejaVu", "", 12)
                pdf.cell(0, 10, f"Рабочий лист по предмету {subject}, {grade} класс", ln=True)
                pdf.ln(5)

                for i, row in df.iterrows():
                    pdf.multi_cell(0, 8, f"{row['№']}. {row['Задание']} ({row['Тип']})")
                    pdf.ln(1)

                pdf_buffer = BytesIO()
                pdf.output(pdf_buffer)
                pdf_buffer.seek(0)

                st.download_button(
                    label="📥 Скачать PDF",
                    data=pdf_buffer,
                    file_name=f"worksheet_{subject}_{grade}kl.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"Ошибка при генерации: {e}")

