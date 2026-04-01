"""
Test suite for ports_adapters.py demonstrating hexagonal architecture testing approach.

This module shows three levels of testing for hexagonal architecture:
1. End-to-end tests: Test complete user journeys through the CLI
2. Integration tests: Test (parts of) the domain in isolation, replacing
   external dependencies with other adapters
3. Unit tests: Test domain logic in isolation
"""

import subprocess

import pytest
from ports_adapters import (
    InMemoryJokesRepository,
    Joke,
    JokeService,
)

# END-TO-END TESTS
# Test complete user journeys through the entire application
# ============================================================================


class TestEndToEnd:
    """
    End-to-end tests for the joke application.

    These tests verify complete user journeys through the application,
    testing the integration of all components.
    """

    def test_list_jokes(self):
        """
        End-to-end test: Add and list jokes.

        Tests the complete flow of listing jokes, including repository
        interaction and service layer processing.
        """
        import shutil
        import os
        
        # Clean up any existing storage files to start with clean state
        storage_dir = "/tmp/jokes_db"
        if os.path.exists(storage_dir):
            shutil.rmtree(storage_dir)
        
        # Run the app by executing ports_adapters.py on the commandline
        output = subprocess.check_output(
            [
                "python",
                "docs/ports_adapters.py",
                "create",
                "Why did the chicken cross the road? To get to the other side.",
            ]
        )
        assert "Why did the chicken cross the road?" in output.decode("utf-8")

        output = subprocess.check_output(["python", "docs/ports_adapters.py", "list"])
        assert "Why did the chicken cross the road?" in output.decode("utf-8")
        
        # Clean up after test
        if os.path.exists(storage_dir):
            shutil.rmtree(storage_dir)


class TestIntegration:
    """
    Integration tests for the joke application.

    These tests verify the interaction between components, ensuring
    that the service layer works correctly with different repository
    implementations.
    """

    def test_list_jokes(self):
        """
        Integration test: Service with InMemoryJokesRepository.

        Tests that the service layer works with the in-memory adapter
        and returns the expected predefined jokes.
        """
        repository = InMemoryJokesRepository()
        repository.jokes = [
            Joke(
                "1", "Why did the chicken cross the road?", "To get to the other side."
            ),
            Joke("2", "What do you call a fake noodle?", "An impasta."),
        ]
        service = JokeService(repository)

        jokes = service.get_jokes()

        # Verify we get the predefined jokes
        assert len(jokes) == 2
        assert jokes[0].title == "Why did the chicken cross the road?"
        assert jokes[1].title == "What do you call a fake noodle?"

    def test_insert_jokes(self):
        """
        Integration test: Service with InMemoryJokesRepository.

        Tests creating jokes through the service layer using the
        in-memory adapter implementation.
        """
        repository = InMemoryJokesRepository()
        service = JokeService(repository)

        # Create multiple jokes
        joke1 = service.create_joke("First joke. This is the body.")
        joke2 = service.create_joke("Second joke? This is also the body.")

        # Verify jokes were created and stored
        jokes = service.get_jokes()
        assert len(jokes) == 2
        assert jokes[0].id == joke1.id
        assert jokes[1].id == joke2.id

    def test_update_joke(self):
        """
        Integration test: Updating jokes through service layer.

        Tests the complete update flow: create → update → verify.
        """
        repository = InMemoryJokesRepository()
        service = JokeService(repository)

        # Create initial joke
        created_joke = service.create_joke("Original joke. Original body.")
        original_id = created_joke.id

        # Update the joke
        updated_joke = service.update_joke(original_id, "Updated joke. Updated body.")

        # Verify update worked
        assert updated_joke.id == original_id  # ID should remain the same
        assert updated_joke.title == "Updated joke."
        assert updated_joke.body == "Updated body."

        # Verify only one joke exists (replaced, not added)
        jokes = service.get_jokes()
        assert len(jokes) == 1
        assert jokes[0].id == original_id


# ============================================================================
# UNIT TESTS
# Test domain logic in isolation
# ============================================================================


class TestJokeDomain:
    """
    Unit tests for the Joke domain model.

    These tests focus on domain logic in complete isolation, testing
    business rules without any infrastructure dependencies.
    """

    def test_joke_parsing_happy_path_with_period(self):
        """
        Unit test: Happy path parsing with period separator.

        Tests the core business rule that jokes must have title/body
        separated by punctuation.
        """
        content = "Why did the chicken cross the road. To get to the other side."
        joke = Joke.from_content(content)

        assert joke.title == "Why did the chicken cross the road."
        assert joke.body == "To get to the other side."
        assert len(joke.id) > 0

    def test_joke_parsing_happy_path_with_question_mark(self):
        """
        Unit test: Happy path parsing with question mark separator.
        """
        content = "What do you call a fake noodle? An impasta."
        joke = Joke.from_content(content)

        assert joke.title == "What do you call a fake noodle?"
        assert joke.body == "An impasta."

    def test_joke_parsing_edge_case_no_punctuation(self):
        """
        Unit test: Edge case with no valid punctuation.

        Tests that the domain enforces its constraints by raising
        appropriate errors for invalid input.
        """
        content = "No punctuation here"

        with pytest.raises(ValueError) as exc_info:
            Joke.from_content(content)

        assert "period or question mark" in str(exc_info.value)

    def test_joke_parsing_edge_case_multiple_punctuation(self):
        """
        Unit test: Edge case with multiple punctuation marks.

        Tests that the parser handles the first valid punctuation
        mark correctly.
        """
        content = "Complex joke. With multiple. Periods? And questions?"
        joke = Joke.from_content(content)

        # Should split on first punctuation (period)
        assert joke.title == "Complex joke."
        assert joke.body == "With multiple. Periods? And questions?"

    def test_joke_parsing_preserves_punctuation_in_title(self):
        """
        Unit test: Punctuation preservation in titles.

        Verifies that punctuation in titles is preserved correctly.
        """
        content = "Why? Because. That's why."
        joke = Joke.from_content(content)

        # Should split on first punctuation (question mark)
        assert joke.title == "Why?"
        assert joke.body == "Because. That's why."


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
