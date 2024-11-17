import streamlit as st
import openai
import os
from pydantic import BaseModel, Field
from typing import List, Literal
import concurrent.futures


# Ustaw klucz API OpenAI
api_key = os.getenv("OPENAI_API_KEY")

st.title("Aplikacja tłumacząca na bezczas")

client = openai.OpenAI(api_key=api_key)

# Wczytaj treść prompta z pliku system_prompts/grammar_selector
with open('system_prompts/grammar_selector', 'r', encoding='utf-8') as file:
    grammar_selector_prompt = file.read()

# Wcztanie gramatyk
def load_files_to_dict(folder_path):
    files_dict = {}
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                files_dict[filename] = file.read()
    return files_dict

folder_path = 'system_prompts/grammars'
grammars = load_files_to_dict(folder_path)


# Wybór języka tłumaczenia
selected_grammar = st.selectbox("Wybierz gramatykę", grammars.keys())

# Pole tekstowe dla zdania do przetłumaczenia
zdanie_do_przetlumaczenia = st.text_area("Zdanie do przetłumaczenia", "")


class Translation(BaseModel):
    original_sentence: str
    timeless_sentence: str

class SentenceGrammar(BaseModel):
    original_sentence: str = Field(..., description="The original sentence provided for grammar application.")
    applicable_grammars: List[Literal[tuple(grammars.keys())]] = Field(..., description="List of grammars applied for the given sentence.")

def call_llm(system_prompt, sentence, validation_class):
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": sentence}
        ],
        response_format=validation_class,
        temperature=0.2
    )
    return response

def translate_sentence():
    return call_llm(grammars[selected_grammar], zdanie_do_przetlumaczenia, Translation)

def select_grammars():
    return call_llm(grammar_selector_prompt, zdanie_do_przetlumaczenia, SentenceGrammar)

# Przycisk "tłumacz"
if st.button("tłumacz"):
    if zdanie_do_przetlumaczenia.strip():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_translation = executor.submit(translate_sentence)
            future_grammars = executor.submit(select_grammars)

            translation = future_translation.result()
            applicable_grammars = future_grammars.result()

        przetlumaczone_zdanie = translation.choices[0].message.parsed.timeless_sentence
        applicable_grammars = applicable_grammars.choices[0].message.parsed.applicable_grammars
    else:
        przetlumaczone_zdanie = "Proszę wpisać zdanie do przetłumaczenia."
        applicable_grammars = []
else:
    przetlumaczone_zdanie = ""
    applicable_grammars = []

# Pole tekstowe dla przetłumaczonego zdania
st.text_area("Przetłumaczone zdanie", przetlumaczone_zdanie)

# Grupa checkboxów dla gramatyk
for grammar in grammars.keys():
    st.checkbox(grammar, value=grammar in applicable_grammars, disabled=True)