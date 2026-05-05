# Travel X UX Defense Text Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the final Russian-language UX defense text (таблица Time-on-Task + законы + 10 эвристик) strictly following the required phrase and evidence rules for Travel X.

**Architecture:** This is a content-only deliverable. The plan creates a single markdown document containing the full defense text. Each task adds a self-contained block (table, laws, heuristics), with explicit wording and UI evidence tied to provided screens.

**Tech Stack:** Markdown only.

---

## File Structure
- Create: `docs/superpowers/plans/2026-05-05-travelx-ux-defense-plan.md` (this plan)
- Create: `docs/ux-defense/travelx-ux-defense-text.md` (final defense text)

### Task 1: Create skeleton document for UX defense text

**Files:**
- Create: `docs/ux-defense/travelx-ux-defense-text.md`

- [ ] **Step 1: Write the initial structure**

```markdown
# Текстовая защита UX-аудита: Travel X

## Time-on-Task

## Законы UX

### Закон Хика

### Закон Фиттса

### Закон Якоба

### Закон Миллера

## Эвристики Нильсена (10 принципов)

1. Видимость состояния системы
2. Сходство с реальным миром
3. Свобода действий
4. Стандарты и согласованность
5. Предотвращение ошибок
6. Узнавание вместо вспоминания
7. Гибкость и эффективность
8. Минимализм
9. Помощь при ошибках
10. Документация и справка
```

- [ ] **Step 2: Quick check (manual)**

Run: `echo "Skeleton created"`
Expected: Prints the message.

- [ ] **Step 3: Commit**

```bash
git add docs/ux-defense/travelx-ux-defense-text.md
git commit -m "docs: add ux defense text skeleton"
```

### Task 2: Fill Time-on-Task table with per-second breakdown

**Files:**
- Modify: `docs/ux-defense/travelx-ux-defense-text.md`

- [ ] **Step 1: Insert the Time-on-Task table**

```markdown
## Time-on-Task

| Сценарий | Микро-шаги и время (с) | Итог (с) |
|---|---|---|
| Регистрация нового аккаунта | 1. Ориентация на странице регистрации (0.8). 2. Поиск формы (0.6). 3. Заполнение имени (3.2). 4. Заполнение email (4.0). 5. Ввод возраста (1.0). 6. Выбор файла фото (1.5). 7. Ввод пароля (3.5). 8. Повтор пароля (3.5). 9. Наведение на CTA «Зарегистрироваться» (0.4). 10. Клик (0.2). 11. Подтверждение перехода на страницу успеха (0.6). | 19.3 |
| Выбор тура (фильтрация + «Подробнее») | 1. Ориентация на странице направлений (0.8). 2. Поиск блока фильтров (0.6). 3. Выбор системы из дропдауна (1.0). 4. Выбор типа объекта (1.0). 5. Выбор активности (1.0). 6. Наведение на «Применить фильтры» (0.4). 7. Клик (0.2). 8. Скан карточек (0.8). 9. Наведение на кнопку «Подробнее» (0.4). 10. Клик (0.2). | 6.4 |
| Бронирование в один клик | 1. Ориентация на главной (0.8). 2. Поиск CTA «Выбрать маршрут» (0.6). 3. Наведение на CTA (0.4). 4. Клик (0.2). | 2.0 |
| Вызов AI-бота | 1. Замечание плавающей кнопки (0.6). 2. Наведение на «AI Ассистент» (0.3). 3. Клик (0.2). | 1.1 |
```

- [ ] **Step 2: Quick check (manual)**

Run: `echo "Table added"`
Expected: Prints the message.

- [ ] **Step 3: Commit**

```bash
git add docs/ux-defense/travelx-ux-defense-text.md
git commit -m "docs: add time-on-task table"
```

### Task 3: Write proofs for 4 UX laws (Hick, Fitts, Jakob, Miller)

**Files:**
- Modify: `docs/ux-defense/travelx-ux-defense-text.md`

- [ ] **Step 1: Insert UX laws proofs**

```markdown
## Законы UX

### Закон Хика
- там на этой странице есть компактный блок фильтров из 3 дропдаунов и 2 кнопок («Применить фильтры», «Сбросить») на странице направлений, что ограничивает число вариантов и ускоряет решение.
- там на этой странице есть один главный CTA «Выбрать маршрут» на главной, поэтому выбор действия не распыляется и решение принимается быстро.

### Закон Фиттса
- там на этой странице есть крупная кнопка «Выбрать маршрут» на главной, расположенная в первом экране, что сокращает время наведения и клика.
- там на этой странице есть большая плавающая кнопка «AI Ассистент» в правом нижнем углу, ее легко захватить курсором и быстро вызвать бот.

### Закон Якоба
- там на этой странице есть привычная верхняя навигация с пунктами «Главная», «Направления», «Войти/Регистрация» (или «Личный кабинет/Выйти»), что совпадает с ожиданиями пользователей веб‑сервисов.
- там на этой странице есть стандартные поля формы регистрации и входа (имя пользователя, пароль), что соответствует привычному паттерну авторизации.

### Закон Миллера
- там на этой странице есть ограниченный набор полей в регистрации (имя, email, возраст, фото, пароль, подтверждение), что укладывается в 7±2 единиц и не перегружает память.
- там на этой странице есть карточная структура профиля в кабинете (возраст, дата регистрации, последнее обновление), что группирует информацию в короткие блоки и снижает когнитивную нагрузку.
```

- [ ] **Step 2: Quick check (manual)**

Run: `echo "Laws added"`
Expected: Prints the message.

- [ ] **Step 3: Commit**

```bash
git add docs/ux-defense/travelx-ux-defense-text.md
git commit -m "docs: add ux laws proofs"
```

### Task 4: Write proofs for Nielsen’s 10 heuristics

**Files:**
- Modify: `docs/ux-defense/travelx-ux-defense-text.md`

- [ ] **Step 1: Insert heuristics proofs**

```markdown
## Эвристики Нильсена (10 принципов)

1. Видимость состояния системы
- там на этой странице есть уведомление «Вход выполнен успешно» в личном кабинете, которое подтверждает результат действия.

2. Сходство с реальным миром
- там на этой странице есть слова «Личный кабинет», «Регистрация», «Войти», которые совпадают с реальными терминами обслуживания клиента.

3. Свобода действий
- там на этой странице есть кнопка «Сбросить» в фильтрах направлений, позволяющая быстро отменить выбор.

4. Стандарты и согласованность
- там на этой странице есть единая стилистика CTA (крупные скругленные кнопки) на главной, в регистрации и в кабинете, что сохраняет консистентность.

5. Предотвращение ошибок
- там на этой странице есть текст «Поддерживаются только JPG, PNG, WEBP и GIF» рядом с загрузкой фото, что предупреждает неверный формат.

6. Узнавание вместо вспоминания
- там на этой странице есть явные подписи полей («Имя пользователя», «Электронная почта», «Пароль») в формах регистрации и входа, поэтому не нужно помнить, что вводить.

7. Гибкость и эффективность
- там на этой странице есть быстрый сценарий «AI Ассистент» через плавающую кнопку, что ускоряет доступ к помощи без навигации.

8. Минимализм
- там на этой странице есть лаконичный hero с одним ключевым CTA и коротким подзаголовком, без лишних элементов первого экрана.

9. Помощь при ошибках
- там на этой странице есть поясняющий текст под полем пароля («Используйте надежный пароль длиной не менее 8 символов»), который подсказывает, как избежать ошибки.

10. Документация и справка
- там на этой странице есть встроенные пояснения к загрузке фото профиля и формату файлов, выполняющие роль микро‑справки.
```

- [ ] **Step 2: Quick check (manual)**

Run: `echo "Heuristics added"`
Expected: Prints the message.

- [ ] **Step 3: Commit**

```bash
git add docs/ux-defense/travelx-ux-defense-text.md
git commit -m "docs: add nielsen heuristics proofs"
```

### Task 5: Final consistency review and formatting polish

**Files:**
- Modify: `docs/ux-defense/travelx-ux-defense-text.md`

- [ ] **Step 1: Consistency checklist**

```markdown
- Проверить, что каждый аргумент содержит фразу «там на этой странице есть» или «там в этой странице есть».
- Проверить, что в таблице указаны все 4 сценария.
- Проверить, что есть 4 закона и 10 эвристик.
- Убедиться, что текст читается как устная защита.
```

- [ ] **Step 2: Quick check (manual)**

Run: `echo "Review done"`
Expected: Prints the message.

- [ ] **Step 3: Commit**

```bash
git add docs/ux-defense/travelx-ux-defense-text.md
git commit -m "docs: finalize ux defense text"
```

---

## Self-Review
1. Spec coverage: Time-on-Task table, 4 UX laws, 10 heuristics, required phrase usage are covered by Tasks 2–4. Skeleton and formatting handled in Tasks 1 and 5.
2. Placeholder scan: no TBD/TODO markers.
3. Type consistency: not applicable (content-only).
