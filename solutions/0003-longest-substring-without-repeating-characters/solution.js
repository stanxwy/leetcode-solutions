/**
 * LeetCode: [0003] Longest Substring Without Repeating Characters
 * Link: https://leetcode.com/problems/longest-substring-without-repeating-characters/
 * Date: 2026-06-16
 * Language: javascript
 * Status: Accepted
 */

/**
 * @param {string} s
 * @return {number}
 */
var lengthOfLongestSubstring = function(s) {
    if (s.length == 0) return 0;
    if (s.length == 1) return 1;
    longest = 0;
    for (i = 0; i < s.length - 1; i++) {
        set = new Set([s[i]]);
        for (j = i + 1; j < s.length; j++) {
            newChar = s[j];
            if (set.has(newChar)) {
                if (set.size > longest)
                    longest = set.size;
                break;
            } else {
                set.add(newChar);
                if (set.size > longest)
                    longest = set.size;
            }
        }
    }
    return longest;
};