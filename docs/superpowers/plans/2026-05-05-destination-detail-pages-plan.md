# Destination Detail Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a dedicated Destination detail page so the catalog stays compact, while booking and reviews move to the detail page with a simplified inline form.

**Architecture:** The catalog template renders short cards with a “Подробнее” link to a new `destination_detail` route. A new detail template renders full Destination data, packages, schedule dropdown, and reviews, and reuses the existing async booking JS (`initAsyncPackageBooking`) and `book_tour_api` endpoint.

**Tech Stack:** Django views/templates, existing `public_site.js`, `public_site.css`.

---

## File Structure & Responsibilities

- Create: `templates/accounts/destination_detail.html`
  - Full Destination page layout: header, package booking form, reviews.

- Modify: `accounts/views.py`
  - Add `destination_detail_view` to fetch a Destination with related packages/schedules/reviews.

- Modify: `accounts/urls.py`
  - Add URL route for the new detail page.

- Modify: `templates/accounts/destinations.html`
  - Shorten cards and link to detail page; remove expanded sections.

- Modify: `static/css/public_site.css`
  - Add minimal layout styles for the new detail page (if needed).

---

### Task 1: Add destination detail view and route

**Files:**
- Modify: `accounts/views.py`
- Modify: `accounts/urls.py`

- [ ] **Step 1: Add view in `accounts/views.py`**

Add a new view below `destinations_view`:

```python
def destination_detail_view(request, destination_id):
    destination = get_object_or_404(
        Destination.objects.annotate(avg_rating=Avg("reviews__rating"))
        .prefetch_related(
            "packages",
            "tags",
            "flight_schedules",
            "reviews__user",
        )
        .select_related("system"),
        pk=destination_id,
    )

    rounded_rating = round(destination.avg_rating or 0)
    destination.rating_stars = "★" * rounded_rating + "☆" * (5 - rounded_rating)
    destination.has_available_seats = any(
        schedule.available_seats > 0 for schedule in destination.flight_schedules.all()
    )

    if request.user.is_authenticated:
        destination.user_can_review = Ticket.objects.filter(
            user=request.user,
            flight_schedule__destination=destination,
        ).exists()
    else:
        destination.user_can_review = False

    return render(
        request,
        "accounts/destination_detail.html",
        {
            "destination": destination,
            "quiz_questions": QUIZ_QUESTIONS,
        },
    )
```

- [ ] **Step 2: Add URL route in `accounts/urls.py`**

```python
path("destinations/<int:destination_id>/", views.destination_detail_view, name="destination_detail"),
```

- [ ] **Step 3: Commit**

```bash
git add accounts/views.py accounts/urls.py
git commit -m "feat: add destination detail route"
```

---

### Task 2: Create destination detail template

**Files:**
- Create: `templates/accounts/destination_detail.html`

- [ ] **Step 1: Add template layout**

```html
{% extends "public_base.html" %}
{% load static %}

{% block title %}{{ destination.title }} | Travel X{% endblock %}

{% block content %}
<section class="container destination-detail">
    <div class="detail-hero">
        <div class="detail-image">
            {% if destination.image %}
                <img src="{{ destination.image.url }}" alt="{{ destination.title }}" onerror="this.onerror=null; this.src='{% static 'images/destination-placeholder.svg' %}';">
            {% else %}
                <img src="{% static 'images/destination-placeholder.svg' %}" alt="{{ destination.title }}">
            {% endif %}
        </div>
        <div class="detail-copy">
            <p class="eyebrow">Космическое направление</p>
            <h1>{{ destination.title }}</h1>
            <p class="destination-meta">{{ destination.system.name }} · {{ destination.get_object_type_display }}</p>
            <p class="lead">{{ destination.description }}</p>
            {% if destination.tags.all %}
                <div class="destination-tags" aria-label="Типы активности">
                    {% for tag in destination.tags.all %}
                        <span>{{ tag.name }}</span>
                    {% endfor %}
                </div>
            {% endif %}
        </div>
    </div>

    <div class="detail-grid">
        <section class="detail-panel">
            <h2>Тарифы и бронирование</h2>
            <div class="package-list">
                {% for package in destination.packages.all %}
                    <div class="package-row">
                        <strong>{{ package.get_class_type_display }}</strong>
                        <span>${{ package.price }}</span>
                        <small>{{ package.features }}</small>
                        {% if destination.flight_schedules.all %}
                            <form method="post" action="{% url 'book_ticket' %}" class="package-booking-form" data-book-url="{% url 'book_tour_api' %}">
                                {% csrf_token %}
                                <input type="hidden" name="package_id" value="{{ package.id }}">
                                <div class="seat-badges" aria-label="Свободные места на рейсах">
                                    {% for schedule in destination.flight_schedules.all %}
                                        <span class="seat-badge{% if schedule.available_seats == 0 %} is-empty{% endif %}">
                                            Осталось мест: {{ schedule.available_seats }}
                                        </span>
                                    {% endfor %}
                                </div>
                                <label>
                                    <span>Рейс</span>
                                    <select name="schedule_id" class="travelx-select" data-custom-select required{% if not destination.has_available_seats %} disabled{% endif %}>
                                        {% for schedule in destination.flight_schedules.all %}
                                            <option value="{{ schedule.id }}" {% if schedule.available_seats == 0 %}disabled{% endif %}>
                                                {{ schedule.departure_at|date:"d.m.Y H:i" }} · мест: {{ schedule.available_seats }}
                                            </option>
                                        {% endfor %}
                                    </select>
                                </label>
                                {% if destination.has_available_seats %}
                                    <div class="package-actions">
                                        <button type="submit" class="book-btn">Оформить заказ</button>
                                        <button type="button" class="btn-buy" data-package-id="{{ package.id }}">Забронировать</button>
                                    </div>
                                {% else %}
                                    <button type="button" class="book-btn is-disabled" disabled>Sold Out</button>
                                {% endif %}
                            </form>
                        {% else %}
                            <small>Расписание рейсов скоро появится.</small>
                        {% endif %}
                    </div>
                {% empty %}
                    <p class="destination-meta">Тарифы скоро появятся.</p>
                {% endfor %}
            </div>
        </section>

        <section class="detail-panel">
            <h2>Отзывы</h2>
            {% for review in destination.reviews.all %}
                <article class="review-card">
                    <div>
                        <strong>{{ review.user.username }}</strong>
                        <span>{{ review.rating }}/5</span>
                    </div>
                    <p>{{ review.text }}</p>
                </article>
            {% empty %}
                <p class="destination-meta">Пока нет отзывов.</p>
            {% endfor %}

            {% if user.is_authenticated %}
                {% if destination.user_can_review %}
                    <form method="post" action="{% url 'add_review' destination.id %}" class="review-form">
                        {% csrf_token %}
                        <label>
                            <span>Рейтинг</span>
                            <select name="rating" class="travelx-select" data-custom-select required>
                                <option value="5">5 — отлично</option>
                                <option value="4">4 — хорошо</option>
                                <option value="3">3 — нормально</option>
                                <option value="2">2 — слабо</option>
                                <option value="1">1 — плохо</option>
                            </select>
                        </label>
                        <label>
                            <span>Отзыв</span>
                            <textarea name="text" rows="3" maxlength="1200" required></textarea>
                        </label>
                        <button type="submit" class="book-btn">Оставить отзыв</button>
                    </form>
                {% else %}
                    <p class="destination-meta">Оставить отзыв можно после покупки билета на это направление.</p>
                {% endif %}
            {% else %}
                <p class="destination-meta">Войдите в аккаунт, чтобы оставить отзыв после путешествия.</p>
            {% endif %}
        </section>
    </div>
</section>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add templates/accounts/destination_detail.html
git commit -m "feat: add destination detail template"
```

---

### Task 3: Shorten catalog cards and link to detail page

**Files:**
- Modify: `templates/accounts/destinations.html`

- [ ] **Step 1: Replace expanded content with compact card actions**

In each card:
- Keep image, title, system/type, short description.
- Keep price tag and 1–2 tags.
- Replace “Подробнее” toggle with a link to the detail page.
- Remove package list and reviews from catalog.

Suggested card footer:

```html
<div class="card-actions">
    <a href="{% url 'destination_detail' dest.id %}" class="book-btn">Подробнее</a>
</div>
```

Optional tag trimming in template:

```html
{% for tag in dest.tags.all|slice:":2" %}
    <span>{{ tag.name }}</span>
{% endfor %}
```

- [ ] **Step 2: Commit**

```bash
git add templates/accounts/destinations.html
git commit -m "feat: shorten catalog cards"
```

---

### Task 4: Add minimal detail page styles

**Files:**
- Modify: `static/css/public_site.css`

- [ ] **Step 1: Add layout styles**

```css
.destination-detail .detail-hero {
    display: grid;
    grid-template-columns: minmax(260px, 1fr) 1.2fr;
    gap: 32px;
    align-items: center;
    margin-bottom: 40px;
}

.destination-detail .detail-image img {
    width: 100%;
    border-radius: 24px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
}

.destination-detail .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 24px;
}

.destination-detail .detail-panel {
    background: rgba(10, 16, 28, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 24px;
}

@media (max-width: 900px) {
    .destination-detail .detail-hero {
        grid-template-columns: 1fr;
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add static/css/public_site.css
git commit -m "style: add destination detail layout"
```

---

### Task 5: Manual checks

**Files:**
- Verify: `templates/accounts/destinations.html`
- Verify: `templates/accounts/destination_detail.html`

- [ ] **Step 1: Manual UI checklist**

1. `/destinations/` shows compact cards and “Подробнее” links.
2. `/destinations/<id>/` shows full content and booking UI.
3. Booking sends JSON and updates button to “Оформлено”.
4. Reviews render and form appears for eligible users.

- [ ] **Step 2: Commit (only if changes required)**

```bash
git add templates/accounts/destinations.html templates/accounts/destination_detail.html static/css/public_site.css
git commit -m "fix: polish destination detail layout"
```

---

## Self-Review

- Spec coverage: new route/view, detail template, compact catalog, async booking, reviews, and minimal styling covered by Tasks 1–5.
- Placeholder scan: no TODO/TBD, concrete code and commands included.
- Type consistency: `destination_detail_view`, `destination_detail` URL name, and template use are consistent.
