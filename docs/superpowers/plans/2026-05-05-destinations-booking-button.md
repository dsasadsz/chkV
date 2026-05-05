# Destinations Booking Button Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit async booking button next to the schedule dropdown in each destination package row.

**Architecture:** Update the existing package booking form markup in the destinations template to wrap actions in a `.package-actions` container and add a `.btn-buy` button. Preserve the current submit button as the fallback.

**Tech Stack:** Django templates, HTML.

---

### Task 1: Add explicit booking button and actions wrapper

**Files:**
- Modify: `templates/accounts/destinations.html`

- [ ] **Step 1: Update the package booking form markup**

Replace the existing submit-only action block inside `.package-booking-form` with the following block (keep the surrounding form structure unchanged):

```html
    {% if dest.has_available_seats %}
        <div class="package-actions">
            <button type="submit" class="book-btn">Оформить заказ</button>
            <button type="button" class="btn-buy" data-package-id="{{ package.id }}">Забронировать</button>
        </div>
    {% else %}
        <button type="button" class="book-btn is-disabled" disabled>Sold Out</button>
    {% endif %}
```

- [ ] **Step 2: Verify placement visually in the template**

Confirm the `.package-actions` block sits inside `.package-row` and below the schedule `<select>` in `templates/accounts/destinations.html`.

- [ ] **Step 3: Commit**

```bash
git add templates/accounts/destinations.html
git commit -m "feat: add explicit async booking button"
```

## Self-Review

**Spec coverage:**
- Add explicit `.btn-buy` button within `.package-actions` wrapper inside `.package-row`: Task 1, Step 1.
- Ensure select is above action buttons: Task 1, Step 2.
- Commit with provided message: Task 1, Step 3.

**Placeholder scan:** No placeholders found.

**Type consistency:** No new types or functions introduced.
