"""
Прямая работа с моделью Qwen БЕЗ веб-сервиса
Загрузка модели и генерация ответов напрямую в коде

Автор: Андрей
Для тим-лида
"""

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


class QwenLocal:

    def __init__(self, model_name: str = "Qwen/Qwen2.5-7B-Instruct"):
        print(f" Загрузка модели {model_name}...")
        print(" Первый запуск скачает модель с HuggingFace (несколько GB)")
        
        # Загрузка токенизатора
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        # Загрузка модели
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,  # float16 для экономии памяти
            device_map="auto",          # Автоматически GPU/CPU
            trust_remote_code=True
        )
        
        print(" Модель загружена и готова к работе!")
    
    def generate_response(
        self, 
        prompt: str, 
        system_message: str = "You are a helpful assistant",
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        # Формируем сообщения в формате чата
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        # Применяем chat template (специальный формат для Qwen)
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Токенизация (превращаем текст в числа)
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        print(f" Генерирую ответ на: '{prompt[:50]}...'")
        
        # ГЕНЕРАЦИЯ ОТВЕТА (здесь происходит магия!)
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=0.95,
            repetition_penalty=1.1
        )
        
        # Убираем промпт из результата (оставляем только ответ)
        generated_ids = [
            output_ids[len(input_ids):] 
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        # Декодируем обратно в текст
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        print(f"Ответ сгенерирован ({len(response)} символов)")
        
        return response
    
    def chat(self, messages: list, max_tokens: int = 512) -> str:
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            do_sample=True,
            top_p=0.95
        )
        
        generated_ids = [
            output_ids[len(input_ids):] 
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        return self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]


# ==================== ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ====================

def example_1():
    # Инициализация 
    qwen = QwenLocal(model_name="Qwen/Qwen2.5-7B-Instruct")
    
    # Генерация ответа
    prompt = "ебани анектод"
    
    print(f" Вопрос:\n{prompt}\n")
    
    answer = qwen.generate_response(
        prompt=prompt,
        system_message="Ты — крутой, веселый чувак",
        max_tokens=300,
        temperature=0.7
    )
    
    print(f"\n Ответ Qwen:\n{answer}\n")
"""
ввод и вывод в терминале:
Загрузка модели Qwen/Qwen2.5-7B-Instruct...
 Первый запуск скачает модель с HuggingFace (несколько GB)
`torch_dtype` is deprecated! Use `dtype` instead!
Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████| 4/4 [00:03<00:00,  1.01it/s]
Some parameters are on the meta device because they were offloaded to the cpu and disk.
 Модель загружена и готова к работе!
 Вопрос:
ебани анектод

 Генерирую ответ на: 'ебани анектод...'
Ответ сгенерирован (257 символов)

 Ответ Qwen:
Извините, но я не могу рассказывать нецензурные анекдоты или истории сексуального характера. Давайте лучше рассмешимся более дружелюбным шуткам или поговорим о чем-нибудь другом! Может быть, вы хотели бы услышать легкий смешной анекдот без грубых выражений?
"""

def example_2_mnogo():
    
    qwen = QwenLocal()
    
    questions = [
        "что такое тахикардия",
        "передается ли через воздух",
        "как предотвратить"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- Вопрос {i} ---")
        print(f" {question}")
        
        answer = qwen.generate_response(
            question, 
            system_message="Ты — врач",
            max_tokens=200,
            temperature=0.6
        )
        
        print(f" {answer}\n")
"""
 Загрузка модели Qwen/Qwen2.5-7B-Instruct...
 Первый запуск скачает модель с HuggingFace (несколько GB)
Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████| 4/4 [00:04<00:00,  1.17s/it]
Some parameters are on the meta device because they were offloaded to the cpu and disk.
 Модель загружена и готова к работе!

--- Вопрос 1 ---
 что такое тахикардия
 Генерирую ответ на: 'что такое тахикардия...'
Ответ сгенерирован (627 символов)
 Тахикардия — это состояние, при котором частота сердечных сокращений превышает норму для данного возраста и состояния здоровья человека. У взрослых нормальная частота покоящегося сердца составляет от 60 до 100 ударов в минуту. При тахикардии этот показатель может достигать более 100 уд/мин даже во время отдыха.

Тахикардия может быть симптомом различных состояний, включая физическую активность, стресс, тревогу или некоторые заболевания сердечно-сосудистой системы. В зависимости от причины и скорости сердцебиения, тахикардию можно классифицировать как:

1. Синусовая тахикардия: наиболее распространенная форма тахикардии,


--- Вопрос 2 ---
 передается ли через воздух
 Генерирую ответ на: 'передается ли через воздух...'
Ответ сгенерирован (231 символов)
 Вопрос передачи чего именно через воздух нужен для более точного ответа? Передаются через воздух различные вирусы и бактерии, а также пыльца растений. Если вы имеете в виду конкретное заболевание или аллерген, пожалуйста, уточните.


--- Вопрос 3 ---
 как предотвратить
 Генерирую ответ на: 'как предотвратить...'
Ответ сгенерирован (227 символов)
 Для того чтобы помочь вам, мне нужно больше информации о том, какую конкретно проблему или состояние вы хотите предотвратить. Это может быть связано со здоровьем, образом жизни, питанием и т.д. Пожалуйста, уточните свой вопрос.
"""
def example_3_history():
    qwen = QwenLocal()
    
    # История диалога
    messages = [
        {"role": "system", "content": "Ты — эксперт по Python"},
        {"role": "user", "content": "Что такое функция?"},
        {"role": "assistant", "content": "Функция в Python — это блок кода, который выполняет определённую задачу."},
        {"role": "user", "content": "Покажи пример простой функции"}
    ]
    
    print("Отправляю диалог с историей...")
    
    answer = qwen.chat(messages, max_tokens=250)
    
    print(f"\n Ответ Qwen:\n{answer}\n")
"""
 Загрузка модели Qwen/Qwen2.5-7B-Instruct...
 Первый запуск скачает модель с HuggingFace (несколько GB)
Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████| 4/4 [00:04<00:00,  1.23s/it]
Some parameters are on the meta device because they were offloaded to the cpu and disk.
 Модель загружена и готова к работе!
Отправляю диалог с историей...

 Ответ Qwen:
Конечно! Вот пример простой функции на Python, которая выводит приветствие:

```python
def greet(name):
    
    print(f"Привет, {name}!")

# Вызов функции
greet("Алиса")
```

В этом примере функция `greet` принимает один аргумент `name` и выводит строку с использованием этого имени. После определения функции она вызывается с аргументом `"Алиса"`, что приводит к выводу сообщения "Привет, Алиса!".
"""

if __name__ == "__main__":
    print(" Прямая работа с Qwen БЕЗ веб-сервиса")
    print(" Модель загружается локально в коде\n")
    
    # Запуск примера 
    example_1()
    example_2_mnogo()
    example_3_history()
    
    print("\n ВСЁ")
