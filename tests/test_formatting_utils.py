"""Tests for formatting utilities."""

import unittest

import pytest

from cor_data_analysis.utils.formatting import (
    format_number, format_percentage, format_currency, format_list,
    truncate_text, format_table, camel_to_snake, snake_to_camel,
    format_phone_number, format_file_size, format_title, format_filename
)


class TestFormattingUtils(unittest.TestCase):
    """Test formatting utility functions."""
    
    def test_format_number(self):
        """Test formatting numbers."""
        # Test basic formatting
        assert format_number(1234.5678) == "1,234.57"
        
        # Test with different decimal places
        assert format_number(1234.5678, decimal_places=0) == "1,235"
        assert format_number(1234.5678, decimal_places=3) == "1,234.568"
        
        # Test with different separators
        assert format_number(1234.5678, thousands_separator=".") == "1.234.57"
        assert format_number(1234.5678, decimal_separator=",") == "1,234,57"
        assert format_number(
            1234.5678, 
            thousands_separator=".", 
            decimal_separator=","
        ) == "1.234,57"
        
        # Test with whole numbers
        assert format_number(1234) == "1,234.00"
    
    def test_format_percentage(self):
        """Test formatting percentages."""
        # Test basic formatting
        assert format_percentage(0.12345) == "12.3%"
        
        # Test with different decimal places
        assert format_percentage(0.12345, decimal_places=0) == "12%"
        assert format_percentage(0.12345, decimal_places=2) == "12.35%"
        
        # Test without percentage symbol
        assert format_percentage(0.12345, include_symbol=False) == "12.3"
        
        # Test with whole numbers
        assert format_percentage(1) == "100.0%"
    
    def test_format_currency(self):
        """Test formatting currency values."""
        # Test basic formatting
        assert format_currency(1234.56) == "$1,234.56"
        
        # Test with different symbols
        assert format_currency(1234.56, symbol="€") == "€1,234.56"
        assert format_currency(1234.56, symbol="£") == "£1,234.56"
        
        # Test with suffix position
        assert format_currency(1234.56, symbol="USD", position="suffix") == "1,234.56 USD"
        
        # Test with different decimal places
        assert format_currency(1234.56, decimal_places=0) == "$1,235"
        assert format_currency(1234.56, decimal_places=3) == "$1,234.560"
        
        # Test with different separators
        assert format_currency(
            1234.56, 
            thousands_separator=".", 
            decimal_separator=","
        ) == "$1.234,56"
    
    def test_format_list(self):
        """Test formatting lists."""
        # Test basic formatting
        assert format_list(["apple", "banana", "orange"]) == "apple, banana and orange"
        
        # Test single item
        assert format_list(["apple"]) == "apple"
        
        # Test empty list
        assert format_list([]) == ""
        
        # Test with custom separators
        assert format_list(["apple", "banana", "orange"], separator="; ") == "apple; banana and orange"
        assert format_list(["apple", "banana", "orange"], last_separator=" or ") == "apple, banana or orange"
        
        # Test with maximum items
        assert format_list(
            ["apple", "banana", "orange", "grape", "melon"], 
            max_items=3
        ) == "apple, banana and orange and 2 more"
        
        # Test with custom "more" text
        assert format_list(
            ["apple", "banana", "orange", "grape", "melon"], 
            max_items=2,
            more_text="plus {count} others"
        ) == "apple and banana plus 3 others"
    
    def test_truncate_text(self):
        """Test truncating text."""
        # Test no truncation needed
        assert truncate_text("Short text", 20) == "Short text"
        
        # Test basic truncation
        assert truncate_text("This is a longer text", 13) == "This is a..."
        
        # Test truncation without keeping words
        assert truncate_text("This is a longer text", 10, keep_words=False) == "This is..."
        
        # Test with custom ellipsis
        assert truncate_text("This is a longer text", 12, ellipsis="[...]") == "This is[...]"
        
        # Test extreme truncation
        assert truncate_text("Too long", 6) == "Too..."
        assert truncate_text("Too long", 5, ellipsis="..") == "Too.."
    
    def test_format_table(self):
        """Test formatting tables."""
        # Test basic table
        data = [
            {"id": 1, "name": "Alice", "score": 95},
            {"id": 2, "name": "Bob", "score": 87},
            {"id": 3, "name": "Charlie", "score": 92}
        ]
        columns = [
            ("id", "ID"),
            ("name", "Name"),
            ("score", "Score")
        ]
        
        expected = (
            "ID | Name    | Score\n"
            "---|---------|----- \n"
            "1  | Alice   | 95   \n"
            "2  | Bob     | 87   \n"
            "3  | Charlie | 92   "
        )
        
        # Remove whitespace for comparison
        formatted_table = format_table(data, columns)
        assert formatted_table.replace(" ", "") == expected.replace(" ", "")
        
        # Test empty data
        assert format_table([], columns) == ""
        assert format_table(data, []) == ""
    
    def test_camel_to_snake(self):
        """Test converting camelCase to snake_case."""
        assert camel_to_snake("camelCase") == "camel_case"
        assert camel_to_snake("snake_case") == "snake_case"  # No change
        assert camel_to_snake("camelCaseTest") == "camel_case_test"
        assert camel_to_snake("CamelCase") == "camel_case"
        assert camel_to_snake("HTTPRequest") == "http_request"
        assert camel_to_snake("URLParser") == "url_parser"
        assert camel_to_snake("isURL") == "is_url"
    
    def test_snake_to_camel(self):
        """Test converting snake_case to camelCase."""
        assert snake_to_camel("snake_case") == "snakeCase"
        assert snake_to_camel("camelCase") == "camelCase"  # No change
        assert snake_to_camel("snake_case_test") == "snakeCaseTest"
        assert snake_to_camel("http_request") == "httpRequest"
        assert snake_to_camel("url_parser") == "urlParser"
        
        # Test with capitalized first letter (Pascal case)
        assert snake_to_camel("snake_case", capitalize_first=True) == "SnakeCase"
        assert snake_to_camel("http_request", capitalize_first=True) == "HttpRequest"
    
    def test_format_phone_number(self):
        """Test formatting phone numbers."""
        # Test standard US number
        assert format_phone_number("1234567890") == "(123) 456-7890"
        
        # Test with country code
        assert format_phone_number("11234567890") == "(123) 456-7890"
        
        # Test with formatting characters
        assert format_phone_number("(123) 456-7890") == "(123) 456-7890"
        assert format_phone_number("123.456.7890") == "(123) 456-7890"
        
        # Test with custom format
        assert format_phone_number(
            "1234567890",
            format_str="+1 {area}-{prefix}-{line}"
        ) == "+1 123-456-7890"
        
        # Test with non-standard length
        assert format_phone_number("12345") == "12345"
    
    def test_format_file_size(self):
        """Test formatting file sizes."""
        assert format_file_size(0) == "0 B"
        assert format_file_size(1023) == "1023.00 B"
        assert format_file_size(1024) == "1.00 KB"
        assert format_file_size(1500) == "1.46 KB"
        assert format_file_size(1024 * 1024) == "1.00 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.00 GB"
        
        # Test negative size
        with pytest.raises(ValueError):
            format_file_size(-100)
    
    def test_format_title(self):
        """Test formatting titles."""
        assert format_title("this is a test") == "This Is A Test"
        
        # Test with "small words"
        assert format_title("the end of the line") == "The End of the Line"
        assert format_title("a day in the life") == "A Day in the Life"
        
        # Test with custom separator
        assert format_title("this-is-a-test", separator="-") == "This-Is-A-Test"
    
    def test_format_filename(self):
        """Test formatting filenames."""
        # Test basic filename
        assert format_filename("test.txt") == "test.txt"
        
        # Test with invalid characters
        assert format_filename("test?.txt") == "test_.txt"
        assert format_filename("test<>:\"/\\|?*.txt") == "test_.txt"
        
        # Test with whitespace and underscores
        assert format_filename(" test_file ") == "test_file"
        assert format_filename("__test__file__") == "test_file"
        
        # Test with maximum length
        long_name = "a" * 300 + ".txt"
        assert len(format_filename(long_name, max_length=255)) <= 255
        
        # Test with extension preservation in long name
        long_name = "a" * 300 + ".txt"
        assert format_filename(long_name, max_length=255).endswith(".txt")
        
        # Test empty name
        assert format_filename("") == "unnamed_file"
        assert format_filename("   ") == "unnamed_file"
