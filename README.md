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

### ❌ What Needs to Be Built

- [ ] User list view and template
- [ ] Conversation view and template
- [ ] Message sending functionality
- [ ] Authentication/authorization
- [ ] HTMX-powered dynamic interactions

## Step-by-Step Implementation Plan

### Step 1: Create the Message Model

- [x] Create a `Message` model with:
  - [x] `sender` (ForeignKey to User)
  - [x] `receiver` (ForeignKey to User)
  - [x] `content` (TextField)
  - [x] `timestamp` (DateTimeField with auto_now_add)

---

### Step 2: Set Up Authentication

- [ ] Implement login/logout views
- [ ] Create login template
- [ ] Add authentication decorators to protected views

---

### Step 3: User List View (User Story 1)

- [ ] Create view to list all users (excluding current user)
- [ ] Create template to display users
- [ ] Use HTMX for dynamic loading if needed
- [ ] Add navigation to conversations

---

### Step 4: Conversation View (User Story 2)

- [ ] Create view to display conversation between current user and selected user
- [ ] Query messages where current user is sender or receiver with selected user
- [ ] Order messages by timestamp
- [ ] Create template to display messages
- [ ] Use HTMX to load messages dynamically

---

### Step 5: Message Sending (User Story 3)

- [ ] Create form for message input
- [ ] Create view to handle POST requests for sending messages
- [ ] Use HTMX to send messages without page reload
- [ ] Update conversation view to show new messages immediately
- [ ] Create message form partial template

---

### Step 6: Enhance HTMX Interactions

- [ ] Add polling for new messages
- [ ] Improve user experience with loading indicators
- [ ] Add smooth scrolling to latest message
- [ ] Handle errors gracefully

---

### Step 7: Styling and Polish

- [ ] Style message bubbles
- [ ] Improve layout and spacing
- [ ] Add responsive design considerations
- [ ] Enhance visual hierarchy

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
│   ├── chat/
│   │   ├── models.py          # Message model
│   │   ├── views.py           # All views (user_list, conversation, send_message)
│   │   ├── urls.py            # App URL patterns
│   │   ├── templates/chat/    # HTML templates
│   │   │   ├── base.html      # Base template (already exists)
│   │   │   ├── home.html      # Home page
│   │   │   ├── user_list.html # User list (to be created)
│   │   │   ├── conversation.html # Conversation view (to be created)
│   │   │   └── message_list.html  # Message list partial (to be created)
│   │   └── static/chat/css/   # Custom CSS
│   └── jbl_chat/
│       ├── settings.py        # Django settings
│       └── urls.py            # Main URL configuration
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose configuration
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
