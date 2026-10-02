# Instagram-Inspired Social Media Application

A Django-based social media web application inspired by core concepts found in platforms such as Instagram.

This project was developed as a **portfolio project** to demonstrate practical experience with Django, Django REST Framework, authentication, relational data modeling, permissions, serializers, forms, class-based views, API development, and automated testing.

The application focuses on the core social interactions of a modern social platform, including user profiles, posts, comments, likes, saved posts, following, blocking, reporting, notifications, and user restrictions.

> **Portfolio project:** This application is intended to demonstrate Django development skills and is not intended to be a production-scale clone of Instagram.

---

## Features

### User Accounts

* User registration and authentication
* Custom user model
* User profiles
* Profile information and profile images
* Editable user information
* Password change functionality
* User-specific profile pages
* Authentication-protected API endpoints

### Profiles

Users can maintain their own profiles containing information such as:

* First name
* Last name
* Username
* Email
* Profile image
* Birthday
* Bio
* Private profile setting

Profile information can be managed through both Django views and REST API endpoints.

---

## Social Connections

The application supports social relationships between users.

### Following

Users can:

* Follow other users
* Receive follow requests
* Accept or manage follow relationships
* View followers and following information
* Determine whether another user is being followed

Follow relationships distinguish between accepted and pending connections.

### Blocking

Users can block other users.

The application uses blocking relationships when determining which content should be visible to a user.

For example, content from a user who has blocked the current user can be excluded from the home feed.

### Restrictions

Users can restrict other users through the restriction API.

Creating a restriction also removes the corresponding existing contact relationships between the two users.

---

## Posts

The application provides a social post system based around the `Message` model.

Users can:

* Create posts
* View posts
* View their own posts
* View posts from followed users
* Delete their own posts
* Interact with posts through likes, comments, saves, and reports

The home feed applies relationship and privacy rules when determining which posts are available to the current user.

---

## Home Feed

The home page provides a personalized feed based on the current user's relationships.

The feed considers:

* The user's own posts
* Posts from users they follow
* Accepted follow relationships
* Block relationships
* Reported posts

For example, a post can be excluded from the feed when:

* Its author is not followed by the current user
* The author has blocked the current user
* The post has been reported by the current user

This logic is implemented in the Django view/queryset layer and covered by automated tests.

---

## Likes

Users can like posts.

The API provides endpoints for:

* Creating a like
* Retrieving likes
* Removing a like

The application also exposes like-related information when serializing social content.

---

## Comments

Users can comment on posts.

The comment system supports:

* Creating comments
* Retrieving comments belonging to a post
* Deleting comments
* Parent comments
* Main comments
* Comment ownership
* Comment likes

Comments are serialized with additional information such as:

* Author information
* Relative creation time
* Whether the comment belongs to the current user
* Like count
* Whether the current user has liked the comment

---

## Comment Likes

Users can like comments.

The API supports:

* Creating comment likes
* Listing comment likes
* Removing comment likes

Comment serialization also provides information about the current user's interaction with a comment.

---

## Saved Posts

Users can save posts for later access.

The application provides endpoints for:

* Saving a post
* Viewing saved posts
* Removing a saved post

Saved content is handled separately from regular post interactions.

---

## Reporting System

The application includes a reporting system for inappropriate or problematic content.

Users can report:

* Posts
* User accounts

Reports are associated with a general reporting reason and the reported object.

The reporting system uses Django's `ContentType` framework and `GenericForeignKey` to support reporting different supported object types.

Users can also submit general problems through a dedicated API endpoint.

---

## Notifications

The application includes a notification system based on Django signals.

For example, creating a follow relationship can generate a notification describing the relationship activity.

Notifications are associated with their originating objects using Django's content types framework.

---

## Privacy and Access Control

The application implements access rules around social relationships and user-owned content.

Examples include:

* Authentication requirements for protected API endpoints
* User ownership checks
* Author-only deletion permissions
* Follow relationship checks
* Blocking relationships
* Private profile information
* Filtering reported content from a user's feed

These rules are implemented using Django and Django REST Framework permissions, querysets, serializers, and view logic.

---

# REST API

A REST API is implemented using **Django REST Framework**.

The API includes endpoints for major application functionality such as:

| Area           | API functionality                             |
| -------------- | --------------------------------------------- |
| Authentication | JWT token and token refresh                   |
| Users          | User listing and search                       |
| Profiles       | Profile creation, retrieval, update, deletion |
| Posts          | Post listing and post detail                  |
| Contacts       | Following/contact relationships               |
| Likes          | Post likes                                    |
| Comments       | Post comments                                 |
| Comment Likes  | Likes on comments                             |
| Saved Posts    | Save and unsave posts                         |
| Reports        | Report posts and users                        |
| Restrictions   | Restrict users                                |
| Password       | Change password                               |
| Messages       | Contact/message submission                    |

### Authentication

The API includes JWT authentication endpoints:

```text
/api/token/
/api/token/refresh/
```

Protected endpoints use Django REST Framework authentication and permission mechanisms.

---

# API Endpoints

The application currently exposes endpoints for functionality including:

```text
/api/
/api/posts/saved/
/api/post/<id>/
/api/users/

/api/contact/
/api/contact/<id>/
/api/conection/<username>/

/api/like/
/api/like/<id>/

/api/profiles/
/api/profiles/<id>

/api/post/<id>/comments
/api/comment/<id>

/api/comments/likes/
/api/comment/likes/<id>

/api/saved/
/api/saved/<id>/

/api/reports/
/api/report/
/api/report-problem/

/api/restriction/<username>/

/api/change-password/

/api/token/
/api/token/refresh/
```

The exact URL prefix depends on the project's root URL configuration.

---

# Django Architecture

The project uses Django's standard application architecture together with Django REST Framework.

The codebase contains separate responsibilities for:

* Models
* Views
* Serializers
* Forms
* URL routing
* Permissions
* Signals
* API endpoints
* Templates
* Static files
* Automated tests

The application makes use of Django features including:

* Class-based views
* Generic views
* Django ORM
* Model relationships
* Generic foreign keys
* Content types
* Signals
* Authentication
* Permissions
* Forms
* Templates
* Queryset filtering
* Django messages
* Django REST Framework serializers
* DRF generic API views

---

# Data Modeling

The application uses relational models to represent social interactions.

The main domain concepts include:

```text
User
 ├── Profile
 ├── Contact
 ├── Block
 ├── Notification
 ├── Message
 ├── Like
 ├── Comment
 ├── LikeComment
 ├── SavePost
 ├── Report
 └── ReportProblem
```

Relationships between users and social objects are handled through Django's ORM and foreign-key relationships.

The reporting system additionally uses Django's `ContentType` framework to associate reports with supported object types.

---

# Forms

Django forms are used where server-rendered functionality requires form handling and validation.

Form-based functionality is integrated with Django's validation and view system rather than duplicating validation logic unnecessarily.

---

# Testing

The project includes an automated test suite built with:

* **pytest**
* **pytest-django**

Tests cover application behavior across different layers of the project, including:

* Models
* Views
* Serializers
* API endpoints
* Authentication
* Permissions
* Ownership rules
* Social relationships
* Feed filtering
* Reporting
* Comments
* Likes
* Saved posts
* Profiles
* Password changes
* Signals

The test suite currently contains **1,077 passing tests**.

Example areas covered by the tests include:

```text
Authentication
    ├── authenticated access
    └── unauthenticated access

Social relationships
    ├── following
    ├── pending relationships
    └── blocking

Posts
    ├── ownership
    ├── feed filtering
    ├── likes
    └── saved posts

Comments
    ├── creation
    ├── ownership
    ├── deletion
    └── comment likes

Reports
    ├── post reports
    ├── user reports
    └── report validation

Profiles
    ├── profile access
    ├── ownership
    └── profile updates

API
    ├── serializers
    ├── permissions
    ├── validation
    └── HTTP behavior
```

Tests are written to validate application behavior rather than Django framework internals.

---

# Code Quality

The project uses automated code-quality tooling including:

* **Ruff**
* **pre-commit**

Ruff is used for linting and formatting, while pre-commit runs the configured checks before commits.

Example:

```bash
pre-commit run --all-files
```

---

# Technology Stack

## Backend

* Python
* Django
* Django REST Framework
* Django ORM
* Django authentication
* Django signals
* Django forms
* JWT authentication

## Testing

* pytest
* pytest-django

## Code Quality

* Ruff
* pre-commit

## Frontend

The project uses Django templates together with HTML, CSS, and JavaScript for the web interface.

---

# Project Structure

A simplified project structure looks like:

```text
project/
│
├── account/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── signals.py
│   └── ...
│
├── social/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── forms.py
│   └── ...
│
├── templates/
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── ...
│
├── tests/
│   └── ...
│
├── manage.py
└── ...
```

The exact structure may differ slightly depending on the local development configuration.

---

# Deployment

The application is intended to be deployed as a portfolio project on **PythonAnywhere**.

The deployment focuses on running the implemented Django application and its REST API in a hosted environment.

The project does **not** claim to implement a production-scale infrastructure comparable to Instagram.

---

# Project Goals

This project was built primarily as a **portfolio project** to demonstrate practical Django development skills.

The main goals were to practice and demonstrate:

* Designing relational Django models
* Building reusable Django views
* Developing REST APIs with DRF
* Implementing authentication and permissions
* Handling user ownership
* Designing social relationships
* Building feed/queryset logic
* Working with Django serializers
* Implementing validation
* Using Django signals
* Working with `ContentType` and generic relations
* Writing comprehensive automated tests
* Maintaining code quality with Ruff and pre-commit
* Structuring a maintainable Django application

---

# Status

This project is an **Instagram-inspired Django social media application developed for portfolio purposes**.

The README intentionally describes the functionality that is implemented in the current codebase rather than presenting planned or future functionality as completed.

---

# License

This project is intended for educational and portfolio purposes.
