import streamlit as st
import openai
import pandas as pd
from fpdf import FPDF
from io import BytesIO

# --- Настройка API ключа через Streamlit Secrets ---
# В Streamlit Cloud: Manage app → Secrets → добавь OPENAI_API_KEY="твой_ключ"
openai.api_key = st.secrets["OPENAI_API_KEY"]

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
                # --- Запрос к OpenAI ---
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

                # --- Преобразуем текст в DataFrame ---
                try:
                    from io import StringIO
                    df = pd.read_csv(StringIO(tasks_text), sep="|")
                except:
                    lines = [line.strip() for line in tasks_text.split("\n") if line.strip() != ""]
                    data = []
                    for idx, line in enumerate(lines, 1):
                        data.append([idx, line, "Задача"])
                    df = pd.DataFrame(data, columns=["№", "Задание", "Тип"])

                st.dataframe(df)

                # --- Генерация PDF ---
                pdf = FPDF()
                pdf.add_page()

                # Подключаем шрифт для кириллицы
                # Файл DejaVuSans.ttf должен лежать рядом с app.py
                pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
                pdf.set_font("DejaVu", "", 12)

                # Заголовок
                pdf.cell(0, 10, f"Рабочий лист по предмету {subject}, {grade} класс", ln=True)
                pdf.ln(5)

                # Добавляем задания
                for i, row in df.iterrows():
                    pdf.multi_cell(0, 8, f"{row['№']}. {row['Задание']} ({row['Тип']})")
                    pdf.ln(1)

                # Сохраняем PDF в буфер для Streamlit
                pdf_buffer = BytesIO()
                pdf_output = pdf.output(dest='S').encode('latin1')
                pdf_buffer.write(pdf_output)
                pdf_buffer.seek(0)

                # Кнопка для скачивания PDF
                st.download_button(
                    label="📥 Скачать PDF",
                    data=pdf_buffer,
                    file_name=f"worksheet_{subject}_{grade}kl.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"Ошибка при генерации: {e}")
