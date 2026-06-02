/**
 * LeetCode: [0001] Two Sum
 * Link: https://leetcode.com/problems/two-sum/
 * Date: 2026-06-01
 * Language: javascript
 * Status: Accepted
 */

/**
 * @param {number[]} nums
 * @param {number} target
 * @return {number[]}
 */
var twoSum = function(nums, target) {
    for (i = 0; i < nums.length - 1; i++) {
        for (j = i + 1; j < nums.length; j++) {
            if (nums[i] + nums[j] === target)
                return [i, j];
        }
    }
};