# jbl-chat

A Django-based messaging application using HTMX for dynamic, interactive frontend experiences.

## Project Overview

This is a messaging startup project built with Django 3.2.8 and HTMX. The application allows users to view other users on the platform, view conversations, and send messages - all with seamless, dynamic interactions powered by HTMX.

## Current State

### ✅ What's Already Set Up

- [x] Django 3.2.8 project structure
- [x] `chat` app created and configured
- [x] Basic URL routing (`chat/urls.py` and main `urls.py`)
- [x] Base template with Bootstrap 5 and HTMX included
- [x] Home view and template (placeholder)
- [x] Docker setup available
- [x] Django REST Framework installed (available for future use)
- [x] Message model (database schema)
- [x] User list view and template
- [x] Conversation view and template
- [x] Message sending functionality
- [x] Authentication/authorization
- [x] HTMX-powered dynamic interactions

## Step-by-Step Implementation Plan

### Step 1: Create the Message Model

- [x] Create a `Message` model with:
  - [x] `sender` (ForeignKey to User)
  - [x] `receiver` (ForeignKey to User)
  - [x] `content` (TextField)
  - [x] `timestamp` (DateTimeField with auto_now_add)

---

### Step 2: Set Up Authentication

- [x] Implement login/logout views
- [x] Create login template
- [x] Add authentication decorators to protected views

---

### Step 3: User List View (User Story 1)

- [x] Create view to list all users (excluding current user)
- [x] Create template to display users
- [x] Use HTMX for dynamic loading if needed
- [x] Add navigation to conversations

---

### Step 4: Conversation View (User Story 2)

- [x] Create view to display conversation between current user and selected user
- [x] Query messages where current user is sender or receiver with selected user
- [x] Order messages by timestamp
- [x] Create template to display messages
- [x] Use HTMX to load messages dynamically

---

### Step 5: Message Sending (User Story 3)

- [x] Create form for message input
- [x] Create view to handle POST requests for sending messages
- [x] Use HTMX to send messages without page reload
- [x] Update conversation view to show new messages immediately
- [x] Create message form partial template

---

### Step 6: Enhance HTMX Interactions

- [x] Add SSE (Server-Sent Events) for real-time message updates (replaces polling)
- [x] Improve user experience with loading indicators
- [x] Add smooth scrolling to latest message
- [x] Handle errors gracefully

---

### Step 7: Styling and Polish

- [x] Style message bubbles
- [x] Improve layout and spacing
- [x] Add responsive design considerations
- [x] Enhance visual hierarchy

---

## How to Run the Project

### Using Docker (Recommended)

```bash
docker-compose up
```

The application will be available at `http://localhost:8000`

---

## Project Structure

```
jbl-chat/
├── jbl_chat/
│   ├── chat/                  # Main chat application
│   │   ├── models.py          # Message and Conversation models
│   │   ├── views.py           # All views (home, user_list, conversation, send_message, etc.)
│   │   ├── urls.py            # Chat app URL patterns
│   │   ├── forms.py           # Message form
│   │   ├── admin.py           # Django admin configuration
│   │   ├── migrations/        # Database migrations
│   │   ├── templates/chat/    # Chat app templates
│   │   │   ├── home.html      # Home page with user list
│   │   │   ├── conversation.html # Conversation view
│   │   │   └── partials/      # HTMX partial templates
│   │   │       ├── _messages.html
│   │   │       ├── _single_message.html
│   │   │       ├── _message_form.html
│   │   │       ├── _user_list.html
│   │   │       ├── _user_list_pagination.html
│   │   │       ├── _load_more_button.html
│   │   │       ├── _load_more_messages.html
│   │   │       ├── _chats_list.html
│   │   │       ├── _contacts_drawer.html
│   │   │       └── _archive_button.html
│   │   ├── static/chat/css/   # Custom CSS
│   │   │   └── custom.css
│   │   └── tests/             # Test files
│   ├── core/                  # Core app (authentication)
│   │   ├── views.py           # Login/logout views
│   │   ├── urls.py            # Core app URL patterns
│   │   └── templates/core/    # Authentication templates
│   │       ├── login.html
│   │       └── partials/
│   │           └── _login_form.html
│   ├── jbl_chat/              # Django project settings
│   │   ├── settings.py        # Django settings
│   │   ├── urls.py            # Main URL configuration
│   │   ├── wsgi.py            # WSGI configuration
│   │   └── asgi.py            # ASGI configuration
│   ├── templates/             # Root-level templates
│   │   ├── base.html          # Base template with HTMX and Bootstrap
│   │   └── partials/          # Shared partial templates
│   │       ├── _messages.html
│   │       ├── _nav_user.html
│   │       └── _pagination.html
│   ├── static/                # Root-level static files
│   │   ├── favicon.png
│   │   └── favicon.svg
│   ├── db.sqlite3             # SQLite database (development)
│   └── manage.py              # Django management script
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose configuration
├── pyproject.toml             # Python project configuration
├── ASSIGNMENT.md              # Original assignment requirements
└── README.md                  # This file
```

---

## Technology Stack

- **Backend:** Django 3.2.8
- **Frontend:** HTMX 2.0.8, Bootstrap 5.2.3
- **Database:** SQLite (development)
- **Authentication:** Django session authentication
- **Containerization:** Docker & Docker Compose

---
