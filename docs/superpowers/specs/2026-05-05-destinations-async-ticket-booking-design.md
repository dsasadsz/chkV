# Design: Destinations Async Ticket Booking

## Goal
Enable ticket purchase on the destinations page with an explicit “Book” button per tour package, sending an async POST to the backend with `package_id` and `schedule_id`, while keeping the existing server-side form flow as a fallback.

## Non-Goals
- Reworking the entire booking flow or psych test UX.
- Removing current form-based booking.
- Changing ticket business rules beyond the async entry point.

## Selected Approach
**Approach 1: keep server-side booking form as fallback, add explicit async “Book” button.**

This keeps a working synchronous flow and adds a JS-powered path with minimal disruption. The async path will call the existing JSON endpoint and display success/error feedback inline via alert and button state updates.

## Components & Changes

### Template: `templates/accounts/destinations.html`
- Add an explicit button for each `TourPackage` row:
  - `<button class="btn-buy" data-package-id="{{ package.id }}">Забронировать</button>`
- Ensure the schedule dropdown is visible above the button and required.
- Keep the existing form markup (including hidden `package_id` and CSRF token) for server-side fallback.
- Provide a data attribute for the booking URL (existing `data-book-url`).

### Styles: existing site CSS
- Add styling for `.btn-buy` to be visually prominent and distinct.
- Include hover state with bright accent (neon outline or vivid fill).

### JS: `static/js/public_site.js`
- Attach click listeners to `.btn-buy`.
- On click:
  - Read `package_id` from `data-package-id`.
  - Read `schedule_id` from the sibling dropdown (required).
  - POST via `fetch` to the booking endpoint with `X-CSRFToken`.
- On success:
  - Show alert “Билет успешно оформлен! Проверьте личный кабинет”.
  - Change button text to “Оформлено”.
- On auth error (401):
  - Show alert “Пожалуйста, войдите в аккаунт”.
  - Optionally use `login_url` if provided by API.

### Backend: `accounts/views.py`
- Reuse `book_tour_api` for async booking.
- Ensure it accepts `package_id` and `schedule_id` and returns JSON:
  - Unauthenticated -> `{status: "error", message: "...", login_url: "..."}` with 401
  - Authenticated -> create `Ticket`, decrement seats, return `{status: "success"}` and metadata

## Data Flow
1. User selects a schedule from dropdown.
2. User clicks `.btn-buy`.
3. JS sends POST to `book_tour_api` with `package_id` + `schedule_id` and CSRF.
4. Backend validates auth and seat availability, creates `Ticket`, decrements seats.
5. JSON response drives UI update.

## Error Handling
- Missing `schedule_id`: JS blocks and shows alert.
- `401` from server: show login prompt and optionally redirect.
- Validation errors (no seats, mismatched package/schedule): show server error message.

## Testing
- Guest click -> alert to login (status 401).
- Auth user with valid schedule -> success alert + button text updates.
- Auth user with sold-out schedule -> error alert.
