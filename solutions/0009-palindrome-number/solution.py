"""
LeetCode: [0009] Palindrome Number
Link: https://leetcode.com/problems/palindrome-number/
Date: 2026-06-03
Language: python3
Status: Accepted
"""

class Solution:
    def isPalindrome(self, x: int) -> bool:
        s = str(x)
        sr = s[::-1]
        return s == sr
        