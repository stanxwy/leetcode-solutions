/**
 * LeetCode: [0002] Add Two Numbers
 * Link: https://leetcode.com/problems/add-two-numbers/
 * Date: 2026-06-03
 * Language: javascript
 * Status: Accepted
 */

/**
 * Definition for singly-linked list.
 * function ListNode(val, next) {
 *     this.val = (val===undefined ? 0 : val)
 *     this.next = (next===undefined ? null : next)
 * }
 */
/**
 * @param {ListNode} l1
 * @param {ListNode} l2
 * @return {ListNode}
 */
var addTwoNumbers = function(l1, l2) {
    let n1 = l1;
    let n2 = l2;
    let curr = null;
    let l3 = null;
    let addOne = false;
    do {
        let v1 = n1 ? n1.val : 0;
        let v2 = n2 ? n2.val : 0;
        let v3 = v1 + v2 + (addOne ? 1 : 0);
        if (v3 >= 10) {
            v3 = v3 % 10;
            addOne = true;
        } else addOne = false;
        
        n1 = n1 ? n1.next: null;
        n2 = n2 ? n2.next : null;
        let n3 = new ListNode(v3, null);

        if (!curr) {
            curr = n3;
            l3 = n3;
        } else {
            curr.next = n3;
            curr = n3;
        }
    } while (!!n1 || !!n2 || addOne)
    return l3;
};