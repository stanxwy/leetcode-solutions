"""
LeetCode: [0001] Two Sum
Link: https://leetcode.com/problems/two-sum/
Date: 2026-06-01
Language: python
Status: Accepted
"""

class Solution(object):
    def twoSum(self, nums, target):
        """
        :type nums: List[int]
        :type target: int
        :rtype: List[int]
        """

        for i, x in enumerate(nums):
            for j, y in enumerate(nums):
                if (i != j) and x + y == target:
                    return i, j


if __name__ == "__main__":
    s = Solution()
    result = s.twoSum([2, 7, 11, 15], 9)
    print(result)