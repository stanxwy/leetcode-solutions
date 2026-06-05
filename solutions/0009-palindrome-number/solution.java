/**
 * LeetCode: [0009] Palindrome Number
 * Link: https://leetcode.com/problems/palindrome-number/
 * Date: 2026-06-05
 * Language: java
 * Status: Accepted
 */

class Solution {
    public boolean isPalindrome(int x) {
        String s = String.valueOf(x);
        int len = s.length();
        for (int i = 0; i <= len / 2; i++) {
            if (s.charAt(i) != s.charAt(len - 1 -i))
                return false;
        }
        return true;
    }
}