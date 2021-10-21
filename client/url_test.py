"""Test functionality for URL manipulation"""

import unittest
from result import Ok
from url import parse_url, url_with_path, unparse_url


class TestURL(unittest.TestCase):
    """Common client functionality test suite"""

    def test_url_append(self):
        """Test parsing URL's and appending to path"""
        # parse url
        url_str = "ws://127.0.0.1:12345"
        url_result = parse_url(url_str)
        self.assertTrue(isinstance(url_result, Ok))
        url = url_result.value

        # append to url
        example_agent_id = "aaf4a840-29d3-11ec-876c-97b00656b091"
        appended_path = f"/client/{example_agent_id}/control"
        agent_url_result = url_with_path(url, appended_path)
        self.assertTrue(isinstance(agent_url_result, Ok))
        agent_url = agent_url_result.value

        # unparse url
        agent_url_str_result = unparse_url(agent_url)
        self.assertTrue(isinstance(agent_url_str_result, Ok))
        agent_url_str = agent_url_str_result.value

        # expect correct outcome
        expectation = f"ws://127.0.0.1:12345/client/{example_agent_id}/control"
        self.assertEqual(agent_url_str, expectation)


if __name__ == '__main__':
    unittest.main()
