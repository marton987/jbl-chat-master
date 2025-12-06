"""
Django management command to populate the database with users.

Usage:
    python manage.py populate_db --admin                    # Create admin/admin superuser
    python manage.py populate_db --users 10                  # Create 10 regular users (user_1/user_1, etc.)
    python manage.py populate_db --admin --users 10         # Create both admin and 10 users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Populate the database with users (admin superuser and/or regular users)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin",
            action="store_true",
            help="Create admin superuser with username 'admin' and password 'admin'",
        )
        parser.add_argument(
            "--users",
            type=int,
            default=0,
            help="Number of regular users to create (format: user_N/user_N)",
        )

    def handle(self, *args, **options):
        create_admin = options["admin"]
        num_users = options["users"]

        if not create_admin and num_users == 0:
            self.stdout.write(
                self.style.WARNING(
                    "No action specified. Use --admin to create admin user or --users N to create N users."
                )
            )
            return

        # Create admin superuser
        if create_admin:
            self.create_admin_user()

        # Create regular users
        if num_users > 0:
            self.create_regular_users(num_users)

    def create_admin_user(self):
        """Create admin superuser with username 'admin' and password 'admin'"""
        username = "admin"
        password = "admin"

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"User '{username}' already exists. Skipping.")
            )
            return

        User.objects.create_superuser(
            username=username,
            email="admin@example.com",
            password=password,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Created superuser '{username}' with password '{password}'"
            )
        )

    def create_regular_users(self, num_users):
        """Create N regular users with format user_N/user_N"""
        created_count = 0
        skipped_count = 0

        for i in range(1, num_users + 1):
            username = f"user_{i}"
            password = f"user_{i}"

            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f"User '{username}' already exists. Skipping.")
                )
                skipped_count += 1
                continue

            User.objects.create_user(
                username=username,
                email=f"user_{i}@example.com",
                password=password,
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Created user '{username}' with password '{password}'"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary: Created {created_count} user(s), skipped {skipped_count} existing user(s)"
            )
        )
