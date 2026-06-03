// lib/leetcode-runner.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');

/**
 * 加载 LeetCode 解决方案文件，无需修改原文件
 * @param {string} solutionPath - solution.js 的路径（绝对路径或相对路径）
 * @returns {Function} - 解决方案中的主函数（假设函数名与文件名相关或取第一个函数）
 */
function loadSolution(solutionPath) {
    // 解析为绝对路径
    const absolutePath = path.resolve(solutionPath);
    
    // 读取文件内容
    const code = fs.readFileSync(absolutePath, 'utf-8');
    
    // 创建沙箱上下文
    const context = {
        console: console,
        setTimeout: setTimeout,
        clearTimeout: clearTimeout,
        setInterval: setInterval,
        clearInterval: clearInterval,
        // 如果 solution.js 中定义了 ListNode，可以在这里传入
        // 但一般 ListNode 是 LeetCode 提供的，在测试文件中定义
    };
    
    vm.createContext(context);
    
    // 执行代码
    vm.runInContext(code, context, { 
        filename: path.basename(absolutePath),
        displayErrors: true
    });
    
    // 尝试从上下文中提取函数
    // 优先级：module.exports > exports > 全局变量
    let result = null;
    
    // 1. 如果有 module.exports
    if (context.module && context.module.exports) {
        result = context.module.exports;
    }
    // 2. 如果有 exports
    else if (context.exports) {
        result = context.exports;
    }
    // 3. 查找常见的函数名
    else {
        const commonNames = [
            'addTwoNumbers',
            'twoSum',
            'solution',
            'Solution',
            'solve'
        ];
        
        for (const name of commonNames) {
            if (typeof context[name] === 'function') {
                result = context[name];
                break;
            }
        }
        
        // 4. 如果还没找到，查找上下文中所有函数，取第一个
        if (!result) {
            const allKeys = Object.keys(context);
            for (const key of allKeys) {
                if (typeof context[key] === 'function' && 
                    !key.startsWith('_') && 
                    key !== 'constructor' &&
                    !['console', 'setTimeout', 'setInterval'].includes(key)) {
                    result = context[key];
                    break;
                }
            }
        }
    }
    
    if (!result) {
        throw new Error(`无法从 ${solutionPath} 中提取到解决方案函数`);
    }
    
    return result;
}

/**
 * 辅助函数：数组转链表
 * @param {Array} arr 
 * @returns {Object} ListNode 头节点
 */
function arrayToList(arr, ListNode) {
    if (!arr || arr.length === 0) return null;
    const dummy = new ListNode(0);
    let current = dummy;
    for (const val of arr) {
        current.next = new ListNode(val);
        current = current.next;
    }
    return dummy.next;
}

/**
 * 辅助函数：链表转数组
 * @param {Object} head - ListNode 头节点
 * @returns {Array}
 */
function listToArray(head) {
    const result = [];
    let current = head;
    while (current) {
        result.push(current.val);
        current = current.next;
    }
    return result;
}

/**
 * 辅助函数：打印链表
 * @param {Object} head - ListNode 头节点
 * @returns {string}
 */
function printList(head) {
    const arr = listToArray(head);
    return arr.join(' -> ');
}

module.exports = {
    loadSolution,
    arrayToList,
    listToArray,
    printList
};