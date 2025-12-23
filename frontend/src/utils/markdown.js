/**
 * Markdown 渲染工具 - 增强版（支持数学公式）
 */
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import katex from 'katex'

// 生成唯一 ID
let codeBlockId = 0
const generateCodeBlockId = () => `code-block-${++codeBlockId}`

// 创建 Markdown 解析器
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: function (str, lang) {
    const id = generateCodeBlockId()
    const langLabel = lang || 'text'
    let highlightedCode = ''
    
    if (lang && hljs.getLanguage(lang)) {
      try {
        highlightedCode = hljs.highlight(str, { language: lang, ignoreIllegals: true }).value
      } catch (__) {
        highlightedCode = md.utils.escapeHtml(str)
      }
    } else {
      highlightedCode = md.utils.escapeHtml(str)
    }
    
    // 对代码内容进行 base64 编码
    const encodedCode = btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, (_, p1) => String.fromCharCode(parseInt(p1, 16))))
    
    return `<div class="code-block-wrapper" data-code="${encodedCode}"><div class="code-block-header"><span class="code-lang-label">${langLabel}</span><button class="code-copy-btn" data-code-id="${id}" onclick="copyCodeBlock('${id}')"><svg class="copy-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg><svg class="check-icon hidden" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg><span class="copy-text">复制</span></button></div><div class="code-scroll-container"><pre class="hljs" id="${id}"><code class="language-${langLabel}">${highlightedCode}</code></pre></div></div>`
  }
})

/**
 * 渲染 KaTeX 公式
 * @param {string} tex - LaTeX 公式
 * @param {boolean} displayMode - 是否为块级公式
 */
const renderKatex = (tex, displayMode = false) => {
  try {
    return katex.renderToString(tex, {
      displayMode,
      throwOnError: false,
      strict: false,
      trust: true,
      macros: {
        "\\text": "\\mathrm"
      }
    })
  } catch (e) {
    console.warn('KaTeX 渲染失败:', e.message, tex)
    return `<span class="katex-error" title="${e.message}">${tex}</span>`
  }
}

/**
 * 预处理数学公式 - 在 markdown 渲染前处理
 * 支持格式：
 * - 块级公式: $$...$$ 或 \[...\]
 * - 行内公式: $...$ 或 \(...\)
 */
const preprocessMath = (text) => {
  if (!text) return text
  
  // 用于存储公式的占位符映射
  const mathPlaceholders = new Map()
  let placeholderIndex = 0
  
  const createPlaceholder = (html) => {
    const placeholder = `%%MATH_PLACEHOLDER_${placeholderIndex++}%%`
    mathPlaceholders.set(placeholder, html)
    return placeholder
  }
  
  // 1. 处理块级公式 $$...$$ (多行支持)
  text = text.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => {
    const html = renderKatex(tex.trim(), true)
    return createPlaceholder(`<div class="katex-block">${html}</div>`)
  })
  
  // 2. 处理块级公式 \[...\] (多行支持)
  text = text.replace(/\\\[([\s\S]*?)\\\]/g, (_, tex) => {
    const html = renderKatex(tex.trim(), true)
    return createPlaceholder(`<div class="katex-block">${html}</div>`)
  })
  
  // 3. 处理行内公式 \(...\)
  text = text.replace(/\\\((.*?)\\\)/g, (_, tex) => {
    const html = renderKatex(tex.trim(), false)
    return createPlaceholder(`<span class="katex-inline">${html}</span>`)
  })
  
  // 4. 处理行内公式 $...$ (避免匹配 $$)
  // 使用更精确的正则：不匹配 $$ 开头，不匹配空内容，不跨行
  text = text.replace(/(?<!\$)\$(?!\$)([^\$\n]+?)\$(?!\$)/g, (_, tex) => {
    // 跳过可能是货币符号的情况（如 $100）
    if (/^\d/.test(tex.trim())) {
      return `$${tex}$`
    }
    const html = renderKatex(tex.trim(), false)
    return createPlaceholder(`<span class="katex-inline">${html}</span>`)
  })
  
  return { text, mathPlaceholders }
}

/**
 * 后处理 - 将占位符替换回公式 HTML
 */
const postprocessMath = (html, mathPlaceholders) => {
  if (!mathPlaceholders || mathPlaceholders.size === 0) return html
  
  for (const [placeholder, mathHtml] of mathPlaceholders) {
    html = html.replace(placeholder, mathHtml)
  }
  
  return html
}

// 自定义表格渲染 - 添加响应式包装器
md.renderer.rules.table_open = function() {
  return '<div class="table-wrapper"><table>'
}

md.renderer.rules.table_close = function() {
  return '</table></div>'
}

// 自定义链接渲染 - 外部链接新标签页打开
const defaultLinkRender = md.renderer.rules.link_open || function(tokens, idx, options, _env, self) {
  return self.renderToken(tokens, idx, options)
}

md.renderer.rules.link_open = function(tokens, idx, options, env, self) {
  const token = tokens[idx]
  const hrefIndex = token.attrIndex('href')
  
  if (hrefIndex >= 0) {
    const href = token.attrs[hrefIndex][1]
    if (href.startsWith('http://') || href.startsWith('https://')) {
      token.attrPush(['target', '_blank'])
      token.attrPush(['rel', 'noopener noreferrer'])
      token.attrPush(['class', 'external-link'])
    }
  }
  
  return defaultLinkRender(tokens, idx, options, env, self)
}

/**
 * 处理引用标记 [1]、[2] 等
 * 支持两种来源：
 * 1. 网络来源（有 url）- 渲染为可点击链接，蓝色
 * 2. 知识库来源（有 content，无 url）- 渲染为可点击按钮，紫色
 */
const processSourceReferences = (html, sources = {}) => {
  // 支持新格式 { webSources: [], kbSources: [] } 和旧格式数组
  let webSources = []
  let kbSources = []
  
  if (Array.isArray(sources)) {
    // 旧格式：根据是否有 url 区分
    sources.forEach(s => {
      if (s.url) {
        webSources.push(s)
      } else {
        kbSources.push(s)
      }
    })
  } else if (sources && typeof sources === 'object') {
    webSources = sources.webSources || []
    kbSources = sources.kbSources || []
  }
  
  if (webSources.length === 0 && kbSources.length === 0) return html
  
  // 匹配 [1]、[2] 等数字引用标记
  const sourcePattern = /\[(\d+)\]/g
  
  return html.replace(sourcePattern, (match, num) => {
    const index = parseInt(num) - 1
    
    // 优先匹配知识库来源（因为 AI 回答中的引用通常是知识库）
    if (index >= 0 && index < kbSources.length) {
      const source = kbSources[index]
      const content = source.content || ''
      // 对内容进行 base64 编码以安全传递
      const encodedContent = btoa(encodeURIComponent(content).replace(/%([0-9A-F]{2})/g, (_, p1) => String.fromCharCode(parseInt(p1, 16))))
      
      return `<button class="source-reference kb-source" data-source-index="${num}" data-source-content="${encodedContent}" onclick="window.showKbSourceDialog && window.showKbSourceDialog(${num}, this.dataset.sourceContent)">[${num}]</button>`
    }
    
    // 其次匹配网络来源
    if (index >= 0 && index < webSources.length) {
      const source = webSources[index]
      const title = source.title || `来源 ${num}`
      return `<a href="${source.url}" target="_blank" rel="noopener noreferrer" class="source-reference web-source" title="${title}">[${num}]</a>`
    }
    
    return match
  })
}

/**
 * 渲染 Markdown 文本（支持数学公式）
 * @param {string} text - Markdown 文本
 * @param {Object} options - 渲染选项
 * @param {Array} options.sources - 引用来源数组
 */
export const renderMarkdown = (text, options = {}) => {
  if (!text) return ''
  
  // 1. 预处理数学公式（替换为占位符）
  const { text: processedText, mathPlaceholders } = preprocessMath(text)
  
  // 2. 渲染 Markdown
  let html = md.render(processedText)
  
  // 3. 后处理：将占位符替换回公式 HTML
  html = postprocessMath(html, mathPlaceholders)
  
  // 4. 处理引用来源
  if (options.sources && options.sources.length > 0) {
    html = processSourceReferences(html, options.sources)
  }
  
  return html
}

/**
 * 渲染行内 Markdown（支持数学公式）
 */
export const renderMarkdownInline = (text) => {
  if (!text) return ''
  
  const { text: processedText, mathPlaceholders } = preprocessMath(text)
  let html = md.renderInline(processedText)
  html = postprocessMath(html, mathPlaceholders)
  
  return html
}

/**
 * 复制代码块内容
 */
if (typeof window !== 'undefined') {
  window.copyCodeBlock = async (id) => {
    const codeElement = document.getElementById(id)
    if (!codeElement) return
    
    const wrapper = codeElement.closest('.code-block-wrapper')
    let code = ''
    
    if (wrapper && wrapper.dataset.code) {
      try {
        code = decodeURIComponent(atob(wrapper.dataset.code).split('').map(c => 
          '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
        ).join(''))
      } catch (e) {
        code = codeElement.textContent || ''
      }
    } else {
      code = codeElement.textContent || ''
    }
    
    const button = document.querySelector(`[data-code-id="${id}"]`)
    
    try {
      await navigator.clipboard.writeText(code)
      
      if (button) {
        const copyIcon = button.querySelector('.copy-icon')
        const checkIcon = button.querySelector('.check-icon')
        const copyText = button.querySelector('.copy-text')
        
        copyIcon?.classList.add('hidden')
        checkIcon?.classList.remove('hidden')
        if (copyText) copyText.textContent = '已复制'
        
        setTimeout(() => {
          copyIcon?.classList.remove('hidden')
          checkIcon?.classList.add('hidden')
          if (copyText) copyText.textContent = '复制'
        }, 2000)
      }
    } catch (err) {
      console.error('复制失败:', err)
    }
  }
}
