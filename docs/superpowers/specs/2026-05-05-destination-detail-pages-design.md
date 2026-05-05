# Design: Destination Detail Pages

## Goal
Move long content out of the destinations catalog by introducing a dedicated detail page per Destination. The catalog cards stay compact (image, title, price, a couple tags, “Подробнее”), while booking, schedules, and reviews live on the detail page with a simplified inline form.

## Non-Goals
- Reworking the booking API or business rules.
- Redesigning the overall site theme.
- Keeping the current modal-based booking flow on destinations.

## Selected Approach
**Approach 1: Dedicated Destination detail page**

Catalog remains a compact grid; each card links to `/destinations/<id>/`. The new detail page includes full description, packages, schedule dropdown, booking button, and reviews. Booking is a simple inline form with the existing async `book_tour_api` endpoint.

## Components & Changes

### Routes & Views
- Add a new view for Destination detail (e.g., `destination_detail_view`) in `accounts/views.py`.
- Add URL route: `path("destinations/<int:destination_id>/", destination_detail_view, name="destination_detail")`.

### Templates
- `templates/accounts/destinations.html`:
  - Keep cards short: image, title, system/type, min price, 1–2 tags, “Подробнее”.
  - Remove expanded package list, schedules, and reviews from the catalog.
- New template: `templates/accounts/destination_detail.html`:
  - Header: image, title, system/type, short lead.
  - Packages + schedule dropdown + “Забронировать” button.
  - Reviews list and review form (same logic as before).
  - Extend `public_base.html` to reuse global styles and scripts.

### JS
- Reuse existing `initAsyncPackageBooking()` handler for `.btn-buy`.
- Ensure `public_site.js` is included on the detail page.

### CSS
- Reuse existing card and booking styles.
- Add minimal layout styles for the detail page (grid/sections) only if required.

## Data Flow
1. User clicks “Подробнее” in catalog.
2. Detail page loads full Destination context and packages/schedules.
3. User selects a schedule and clicks “Забронировать”.
4. JS sends JSON POST to `book_tour_api` with `package_id` and `schedule_id`.
5. Backend returns JSON; UI shows alert and updates button text to “Оформлено”.

## Error Handling
- Missing schedule selection: JS shows alert and blocks request.
- Unauthenticated user: API returns 401; JS shows “Пожалуйста, войдите в аккаунт”.
- Sold-out or invalid selection: API returns error message; JS shows alert.

## Testing
- Catalog: cards are compact, “Подробнее” navigates to detail page.
- Detail page renders packages, schedules, and reviews correctly.
- Async booking succeeds for logged-in user with available seats.
- Booking fails with clear alert for guests or sold-out schedules.
