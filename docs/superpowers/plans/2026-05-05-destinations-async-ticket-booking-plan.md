# Destinations Async Ticket Booking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit “Book” button per tour package that sends an async booking request with `package_id` and `schedule_id` while keeping the existing server-side form as a fallback.

**Architecture:** The template continues to render the package booking form and schedule dropdown. A new `.btn-buy` button triggers a JS fetch to `book_tour_api` with CSRF and selected `schedule_id`. The API already handles booking logic and returns JSON; UI updates occur based on the response.

**Tech Stack:** Django templates, Django views, vanilla JS (Fetch), existing site CSS.

---

## File Structure & Responsibilities

- Modify: `templates/accounts/destinations.html`
  - Render explicit `.btn-buy` button per package row.
  - Ensure schedule dropdown is visible above the button.
  - Keep current form-based booking (fallback).

- Modify: `static/js/public_site.js`
  - Add click listener for `.btn-buy` buttons.
  - Send `package_id` + `schedule_id` to `book_tour_api` with CSRF.
  - Update button text and show success/error alerts.

- Modify: `static/css/public_site.css` (or existing site CSS file where buttons are styled)
  - Add `.btn-buy` styles with a visible neon/bright hover state.

- Verify: `accounts/views.py`
  - Ensure `book_tour_api` accepts `package_id` and `schedule_id` and returns JSON.

---

### Task 1: Add explicit booking button and schedule dropdown placement

**Files:**
- Modify: `templates/accounts/destinations.html`

- [ ] **Step 1: Update markup to include `.btn-buy`**

Add a button inside each `.package-row` near the schedule dropdown, keeping the existing form:

```html
<form method="post" action="{% url 'book_ticket' %}" class="package-booking-form" data-book-url="{% url 'book_tour_api' %}">
    {% csrf_token %}
    <input type="hidden" name="package_id" value="{{ package.id }}">
    <div class="seat-badges" aria-label="Свободные места на рейсах">
        {% for schedule in dest.flight_schedules.all %}
            <span class="seat-badge{% if schedule.available_seats == 0 %} is-empty{% endif %}">
                Осталось мест: {{ schedule.available_seats }}
            </span>
        {% endfor %}
    </div>
    <label>
        <span>Рейс</span>
        <select name="schedule_id" class="travelx-select" data-custom-select required{% if not dest.has_available_seats %} disabled{% endif %}>
            {% for schedule in dest.flight_schedules.all %}
                <option value="{{ schedule.id }}" {% if schedule.available_seats == 0 %}disabled{% endif %}>
                    {{ schedule.departure_at|date:"d.m.Y H:i" }} · мест: {{ schedule.available_seats }}
                </option>
            {% endfor %}
        </select>
    </label>
    {% if dest.has_available_seats %}
        <div class="package-actions">
            <button type="submit" class="book-btn">Оформить заказ</button>
            <button type="button" class="btn-buy" data-package-id="{{ package.id }}">Забронировать</button>
        </div>
    {% else %}
        <button type="button" class="book-btn is-disabled" disabled>Sold Out</button>
    {% endif %}
</form>
```

- [ ] **Step 2: Sanity-check HTML structure in the template**

Ensure that the button sits inside `.package-row` and that the select is above it visually.

- [ ] **Step 3: Commit**

```bash
git add templates/accounts/destinations.html
git commit -m "feat: add explicit async booking button"
```

---

### Task 2: Add JS handler for async booking

**Files:**
- Modify: `static/js/public_site.js`

- [ ] **Step 1: Add a click handler for `.btn-buy`**

Insert a helper in `initAsyncTourBooking()` or create a new function:

```js
function initAsyncPackageBooking() {
    document.querySelectorAll(".btn-buy").forEach((button) => {
        button.addEventListener("click", async () => {
            const form = button.closest("form.package-booking-form");
            if (!form) {
                return;
            }

            const scheduleSelect = form.querySelector("select[name=\"schedule_id\"]");
            const scheduleId = scheduleSelect?.value || "";
            const packageId = button.dataset.packageId || "";
            if (!scheduleId || !packageId) {
                alert("Выберите рейс для бронирования.");
                return;
            }

            const defaultText = button.textContent;
            button.disabled = true;
            button.textContent = "Бронируем...";

            try {
                const response = await fetch(form.dataset.bookUrl, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(form),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify({
                        package_id: packageId,
                        schedule_id: scheduleId,
                    }),
                });
                const data = await response.json();

                if (!response.ok || data.status !== "success") {
                    throw new Error(data.message || "Не удалось забронировать тур.");
                }

                alert("Билет успешно оформлен! Проверьте личный кабинет");
                button.textContent = "Оформлено";
            } catch (error) {
                alert(error.message || "Ошибка бронирования. Попробуйте еще раз.");
                button.disabled = false;
                button.textContent = defaultText;
            }
        });
    });
}
```

- [ ] **Step 2: Call the new initializer on page load**

```js
initAsyncPackageBooking();
```

- [ ] **Step 3: Commit**

```bash
git add static/js/public_site.js
git commit -m "feat: add async booking fetch handler"
```

---

### Task 3: Style the “Book” button

**Files:**
- Modify: `static/css/public_site.css`

- [ ] **Step 1: Add styles for `.btn-buy`**

```css
.btn-buy {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 18px;
    border-radius: 999px;
    border: 1px solid rgba(0, 255, 136, 0.6);
    background: rgba(0, 255, 136, 0.08);
    color: #d5ffe9;
    font-weight: 600;
    letter-spacing: 0.2px;
    transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.btn-buy:hover {
    transform: translateY(-1px);
    box-shadow: 0 0 12px rgba(0, 255, 136, 0.55);
    background: rgba(0, 255, 136, 0.16);
}

.btn-buy:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    box-shadow: none;
}

.package-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}
```

- [ ] **Step 2: Commit**

```bash
git add static/css/public_site.css
git commit -m "style: add neon booking button"
```

---

### Task 4: Verify API behavior and manual checks

**Files:**
- Verify: `accounts/views.py`

- [ ] **Step 1: Confirm `book_tour_api` supports JSON and `schedule_id`**

No code change needed if it already accepts JSON and both IDs.

- [ ] **Step 2: Manual test checklist**

1. As guest, click “Забронировать” -> alert to login (HTTP 401).
2. As logged-in user, select schedule + click -> success alert + button text “Оформлено”.
3. Select sold-out schedule -> error alert.

- [ ] **Step 3: Commit (if any view changes are needed)**

```bash
git add accounts/views.py
git commit -m "fix: align booking API responses"
```

---

## Self-Review

- Spec coverage: template button + JS fetch + schedule dropdown + API behavior + UI messaging all covered by tasks 1-4.
- Placeholder scan: no TODO/TBD, concrete code and commands included.
- Type consistency: `package_id` and `schedule_id` used consistently across JS and API.
