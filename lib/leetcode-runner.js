// lib/leetcode-runner.js
import fs from 'fs';
import path from 'path';
import vm from 'vm';

/**
 * 加载 LeetCode 解决方案文件
 * @param {string} solutionPath - solution.js 的路径
 * @param {Object} dependencies - 外部依赖（如 ListNode, TreeNode 等）
 * @returns {Promise<Function>} - 解决方案函数
 */
export async function loadSolution(solutionPath, dependencies = {}) {
    const absolutePath = path.resolve(solutionPath);
    const code = fs.readFileSync(absolutePath, 'utf-8');
    
    // 创建沙箱上下文，注入依赖
    const context = {
        console: console,
        setTimeout: setTimeout,
        clearTimeout: clearTimeout,
        setInterval: setInterval,
        clearInterval: clearInterval,
        Buffer: Buffer,
        process: process,
        // 注入外部依赖
        ...dependencies,
    };
    
    vm.createContext(context);
    
    // 执行代码
    vm.runInContext(code, context, { 
        filename: path.basename(absolutePath),
        displayErrors: true
    });
    
    // 提取函数
    const solutionFn = extractFunction(context);
    
    if (!solutionFn) {
        throw new Error(`无法从 ${solutionPath} 中提取到解决方案函数`);
    }
    
    return solutionFn;
}

function extractFunction(context) {
    // 1. 检查 module.exports
    if (context.module && context.module.exports) {
        const exp = context.module.exports;
        if (typeof exp === 'function') return exp;
        if (exp && typeof exp === 'object') {
            for (const key of Object.keys(exp)) {
                if (typeof exp[key] === 'function') return exp[key];
            }
        }
    }
    
    // 2. 检查 exports
    if (context.exports && typeof context.exports === 'object') {
        for (const key of Object.keys(context.exports)) {
            if (typeof context.exports[key] === 'function') return context.exports[key];
        }
    }
    
    // 3. 常见函数名
    const commonNames = [
        'addTwoNumbers', 'twoSum', 'solution', 'solve',
        'longestPalindrome', 'maxArea', 'threeSum'
    ];
    for (const name of commonNames) {
        if (typeof context[name] === 'function') return context[name];
    }
    
    // 4. 查找所有函数
    const allKeys = Object.keys(context);
    for (const key of allKeys) {
        const val = context[key];
        if (typeof val === 'function' && 
            !key.startsWith('_') && 
            key !== 'constructor' &&
            !['console', 'setTimeout', 'setInterval', 'require', 'module', 'exports', 'Buffer', 'process'].includes(key) &&
            val.length >= 1) {
            return val;
        }
    }
    
    return null;
}

// 辅助函数
export function arrayToList(arr, ListNode) {
    if (!arr || arr.length === 0) return null;
    const dummy = new ListNode(0);
    let current = dummy;
    for (const val of arr) {
        current.next = new ListNode(val);
        current = current.next;
    }
    return dummy.next;
}

export function listToArray(head) {
    const result = [];
    let current = head;
    while (current) {
        result.push(current.val);
        current = current.next;
    }
    return result;
}

export function printList(head) {
    const arr = listToArray(head);
    return arr.join(' -> ');
}