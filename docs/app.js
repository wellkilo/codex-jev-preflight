(() => {
  "use strict";

  const translations = {
    en: {
      "a11y.skip": "Skip to content",
      "brand.subtitle": "TypeSafe Jev for Codex hooks",
      "nav.how": "How it works",
      "nav.quick": "Quick start",
      "nav.demo": "Demo",
      "nav.docs": "Docs",
      "hero.eyebrow": "Codex UserPromptSubmit Hook",
      "hero.title": "A preflight check for every Codex task.",
      "hero.lead": "Ask TypeSafe Jev for task type, complexity, risk, and execution mode before Codex starts working. Advisory only. Fail-open by design.",
      "hero.primary": "Start in 60 seconds",
      "hero.secondary": "Try the demo",
      "hero.point1": "Never blocks a task",
      "hero.point2": "Zero Python dependencies",
      "hero.point3": "Persistent quota breaker",
      "hero.caption": "Live hook flow, visualized",
      "stats.task": "task types",
      "stats.complexity": "complexity levels",
      "stats.risk": "risk levels",
      "stats.modes": "execution modes",
      "stats.deps": "third-party deps",
      "how.kicker": "How it works",
      "how.title": "One request. Four useful signals.",
      "how.lead": "The hook runs before Codex starts the task and adds a compact assessment to the current turn.",
      "how.step1.title": "Prompt arrives",
      "how.step1.body": "Codex forwards the new user prompt to the UserPromptSubmit hook.",
      "how.step2.title": "Jev assesses",
      "how.step2.body": "One structured request returns four routing choices.",
      "how.step3.title": "Values validated",
      "how.step3.body": "Only declared enum values are injected into Codex context.",
      "how.step4.title": "Codex continues",
      "how.step4.body": "Jev advises. Codex remains responsible for the task.",
      "quick.kicker": "Quick start",
      "quick.title": "Install it with one prompt.",
      "quick.lead": "Paste this into Codex. It will read the README, install the project, ask for the API key with hidden input, and verify the hook.",
      "quick.promptLabel": "Recommended: paste this into Codex",
      "quick.copyPrompt": "Copy prompt",
      "quick.installPrompt": `Install and configure Codex Jev Preflight from https://github.com/wellkilo/codex-jev-preflight.

Requirements:
1. Read the repository README first.
2. Install the project from source.
3. Run codex-jev-configure and ask me to enter the TypeSafe Jev API key with hidden input. Never ask me to paste the key into chat.
4. Run codex-jev-install and verify the hook output.
5. Preserve existing hooks.json and AGENTS.md configuration.
6. Tell me whether Codex must be restarted or a new task must be opened.`,
      "quick.manual.title": "Manual install",
      "quick.configure.title": "Configure and install",
      "quick.copy": "Copy",
      "usage.kicker": "After installation",
      "usage.title": "No per-prompt commands required.",
      "usage.body": "Submit normal Codex tasks. The hook adds the assessment automatically.",
      "usage.chip1": "Security review",
      "usage.chip2": "Feature work",
      "usage.chip3": "Research",
      "demo.kicker": "Interactive preview",
      "demo.title": "See the assessment shape.",
      "demo.lead": "This local demo explains the four fields. The installed hook receives the real result from Jev.",
      "demo.inputLabel": "Enter a Codex task",
      "demo.sample1": "Simple task",
      "demo.sample2": "Moderate build",
      "demo.sample3": "High risk",
      "demo.run": "Generate assessment",
      "demo.note": "Local simulation only. No network request is made.",
      "demo.outputSub": "automatic, advisory routing metadata",
      "demo.local": "LOCAL DEMO",
      "demo.confidence": "Demo confidence",
      "docs.kicker": "Documentation",
      "docs.title": "Everything needed to ship safely.",
      "docs.card1.title": "Install, configure, verify",
      "docs.card1.body": "Complete setup, environment variables, troubleshooting, and uninstall steps.",
      "docs.card2.title": "Hooks, fallback, circuit breaker",
      "docs.card2.body": "Understand the request flow and every fail-open path.",
      "docs.card3.title": "Data boundary and reporting",
      "docs.card3.body": "See exactly what leaves the machine and how to report a vulnerability.",
      "docs.read": "Read documentation →",
      "docs.inspect": "Inspect architecture →",
      "docs.security": "Read security notes →",
      "cta.kicker": "Ready to preflight?",
      "cta.title": "Give Codex a consistent first decision.",
      "cta.primary": "Get started",
      "cta.secondary": "View source",
      "footer.note": "MIT License · Not affiliated with OpenAI, Codex, TypeSafe, or Jev.",
      "toast.copied": "Copied to clipboard",
      "toast.copyFailed": "Copy failed. Select the text manually.",
      "toast.empty": "Enter a task first.",
      "language.aria": "Switch language",
      "nav.open": "Open navigation",
    },
    zh: {
      "a11y.skip": "跳到主要内容",
      "brand.subtitle": "为 Codex Hook 接入 TypeSafe Jev",
      "nav.how": "工作原理",
      "nav.quick": "快速开始",
      "nav.demo": "交互演示",
      "nav.docs": "文档",
      "hero.eyebrow": "Codex UserPromptSubmit Hook",
      "hero.title": "让每个 Codex 任务先做一次预检。",
      "hero.lead": "Codex 开始执行前，先向 TypeSafe Jev 获取任务类型、复杂度、风险和执行模式。结果仅作建议，并始终 fail-open。",
      "hero.primary": "60 秒快速开始",
      "hero.secondary": "试用交互演示",
      "hero.point1": "绝不阻塞任务",
      "hero.point2": "零 Python 依赖",
      "hero.point3": "持久化额度熔断",
      "hero.caption": "Hook 流程可视化",
      "stats.task": "任务类型",
      "stats.complexity": "复杂度等级",
      "stats.risk": "风险等级",
      "stats.modes": "执行模式",
      "stats.deps": "第三方依赖",
      "how.kicker": "工作原理",
      "how.title": "一次请求，四项有效信号。",
      "how.lead": "Hook 在 Codex 开始执行前运行，并把紧凑的判定结果加入当前任务。",
      "how.step1.title": "收到用户提示",
      "how.step1.body": "Codex 将新提示交给 UserPromptSubmit Hook。",
      "how.step2.title": "Jev 进行判定",
      "how.step2.body": "一次结构化请求返回四个路由选择。",
      "how.step3.title": "校验返回枚举",
      "how.step3.body": "只有已声明的枚举值才会注入 Codex 上下文。",
      "how.step4.title": "Codex 继续执行",
      "how.step4.body": "Jev 提供建议，最终仍由 Codex 负责完成任务。",
      "quick.kicker": "快速开始",
      "quick.title": "用一段 Prompt 完成安装。",
      "quick.lead": "把下面的 Prompt 粘贴给 Codex。它会读取 README、安装项目、用隐藏输入配置 API Key，并验证 Hook。",
      "quick.promptLabel": "推荐：把以下内容粘贴给 Codex",
      "quick.copyPrompt": "复制 Prompt",
      "quick.installPrompt": `请安装并配置 Codex Jev Preflight。

要求：
1. 阅读 https://github.com/wellkilo/codex-jev-preflight 的 README。
2. 从源码安装项目。
3. 运行 codex-jev-configure，API Key 必须隐藏输入，不要要求我在聊天中粘贴。
4. 运行 codex-jev-install 并验证 Hook 输出。
5. 不要覆盖现有的 hooks.json 和 AGENTS.md 配置。
6. 告诉我需要重启 Codex 还是新建任务。`,
      "quick.manual.title": "手动安装",
      "quick.configure.title": "配置并安装",
      "quick.copy": "复制",
      "usage.kicker": "安装完成后",
      "usage.title": "无需在每条任务中手动调用。",
      "usage.body": "正常提交 Codex 任务，Hook 会自动加入判定上下文。",
      "usage.chip1": "安全审查",
      "usage.chip2": "功能开发",
      "usage.chip3": "技术调研",
      "demo.kicker": "交互预览",
      "demo.title": "查看实际判定结构。",
      "demo.lead": "这是用于解释四个字段的前端模拟。正式安装后，真实结果来自 Jev API。",
      "demo.inputLabel": "输入一个 Codex 任务",
      "demo.sample1": "简单任务",
      "demo.sample2": "中等开发",
      "demo.sample3": "高风险任务",
      "demo.run": "生成判定结果",
      "demo.note": "仅做本地模拟，不会发送网络请求。",
      "demo.outputSub": "自动生成的建议性路由元数据",
      "demo.local": "本地演示",
      "demo.confidence": "演示置信度",
      "docs.kicker": "文档",
      "docs.title": "安全使用所需的全部信息。",
      "docs.card1.title": "安装、配置与验证",
      "docs.card1.body": "完整操作步骤、环境变量、故障排查和卸载说明。",
      "docs.card2.title": "Hook、回退与额度熔断",
      "docs.card2.body": "了解完整请求流程和所有 fail-open 降级路径。",
      "docs.card3.title": "数据边界与漏洞报告",
      "docs.card3.body": "明确哪些数据会离开本机，以及如何报告安全问题。",
      "docs.read": "阅读文档 →",
      "docs.inspect": "查看架构 →",
      "docs.security": "查看安全说明 →",
      "cta.kicker": "准备开始？",
      "cta.title": "让 Codex 拥有稳定的第一判断。",
      "cta.primary": "立即开始",
      "cta.secondary": "查看源码",
      "footer.note": "MIT License · 非 OpenAI、Codex、TypeSafe 或 Jev 官方项目。",
      "toast.copied": "已复制到剪贴板",
      "toast.copyFailed": "复制失败，请手动选择文本。",
      "toast.empty": "请先输入一个任务。",
      "language.aria": "切换语言",
      "nav.open": "打开导航",
    },
  };

  const header = document.querySelector(".site-header");
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector(".nav-links");
  const languageToggle = document.getElementById("language-toggle");
  const languageCurrent = document.querySelector(".language-current");
  const promptInput = document.getElementById("demo-prompt");
  const runButton = document.getElementById("run-demo");
  const toast = document.getElementById("copy-toast");
  let currentLanguage = document.documentElement.dataset.lang === "zh" ? "zh" : "en";
  let toastTimer = 0;

  function t(key) {
    return translations[currentLanguage][key] || translations.en[key] || key;
  }

  function getStoredLanguage() {
    try {
      return localStorage.getItem("codex-jev-language");
    } catch (_) {
      return null;
    }
  }

  function storeLanguage(language) {
    try {
      localStorage.setItem("codex-jev-language", language);
    } catch (_) {}
  }

  function setHeaderState() {
    if (header) header.classList.toggle("scrolled", window.scrollY > 12);
  }

  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 1800);
  }

  function applyLanguage(language) {
    currentLanguage = language === "zh" ? "zh" : "en";
    document.documentElement.dataset.lang = currentLanguage;
    document.documentElement.lang = currentLanguage === "zh" ? "zh-CN" : "en";
    document.querySelectorAll("[data-i18n]").forEach((element) => {
      element.textContent = t(element.dataset.i18n);
    });
    if (languageCurrent) languageCurrent.textContent = currentLanguage === "en" ? "中文" : "EN";
    if (languageToggle) languageToggle.setAttribute("aria-label", t("language.aria"));
    if (navToggle) navToggle.setAttribute("aria-label", t("nav.open"));
    storeLanguage(currentLanguage);
    runDemo();
  }

  function updateDemoPromptForLanguage() {
    if (!promptInput) return;
    const previousEn = "Refactor authentication and migrate the database while keeping the public API compatible.";
    const previousZh = "重构认证模块并迁移数据库，需要保持现有 API 兼容。";
    if (!promptInput.value.trim() || promptInput.value === previousEn || promptInput.value === previousZh) {
      promptInput.value = currentLanguage === "zh" ? previousZh : previousEn;
    }
  }

  setHeaderState();
  window.addEventListener("scroll", setHeaderState, { passive: true });

  if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => {
      const open = navLinks.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", String(open));
    });
    navLinks.addEventListener("click", (event) => {
      if (event.target instanceof HTMLElement && event.target.closest("a")) {
        navLinks.classList.remove("open");
        navToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  if (languageToggle) {
    languageToggle.addEventListener("click", () => {
      const next = currentLanguage === "en" ? "zh" : "en";
      currentLanguage = next;
      updateDemoPromptForLanguage();
      applyLanguage(next);
    });
  }

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }

  document.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const copyButton = target.closest("[data-copy-target]");
    if (!(copyButton instanceof HTMLElement)) return;
    const source = document.getElementById(copyButton.dataset.copyTarget || "");
    if (!source) return;
    try {
      await copyText(source.innerText);
      showToast(t("toast.copied"));
    } catch (_) {
      showToast(t("toast.copyFailed"));
    }
  });

  const keywordGroups = {
    code_change: ["code", "bug", "refactor", "test", "implement", "feature", "代码", "修复", "重构", "测试", "功能", "实现"],
    research: ["research", "compare", "analysis", "search", "调研", "对比", "分析", "搜索", "资料"],
    browser_automation: ["browser", "website", "click", "form", "网页", "浏览器", "点击", "表单"],
    planning: ["plan", "architecture", "strategy", "roadmap", "方案", "架构", "规划", "路线图"],
    answer: ["explain", "what is", "how does", "解释", "是什么", "回答", "说明"],
    conversation: ["brainstorm", "discuss", "讨论", "头脑风暴", "聊聊"],
  };

  const complexWords = ["architecture", "migration", "migrate", "cross-file", "multiple", "production", "database", "security", "架构", "迁移", "跨文件", "多个文件", "生产", "数据库", "安全", "并发"];
  const highRiskWords = ["production", "deploy", "deployment", "delete", "drop table", "credential", "payment", "生产", "部署", "删除", "数据库表", "凭据", "密钥", "支付"];
  const mediumRiskWords = ["write", "modify", "refactor", "migrate", "commit", "push", "修改", "写入", "重构", "迁移", "提交", "推送"];
  const vagueWords = ["not sure", "ambiguous", "unclear", "不清楚", "不确定", "需要确认"];

  function includesAny(text, words) {
    return words.some((word) => text.includes(word));
  }

  function classifyPrompt(rawPrompt) {
    const prompt = rawPrompt.trim().toLowerCase();
    let taskType = "other";
    let complexity = "simple";
    let risk = "low";
    let executionMode = "inspect_then_act";
    let confidence = 62;

    for (const [type, words] of Object.entries(keywordGroups)) {
      if (includesAny(prompt, words)) {
        taskType = type;
        confidence += 6;
        break;
      }
    }

    if (includesAny(prompt, complexWords) || rawPrompt.length > 90) {
      complexity = "moderate";
      confidence += 6;
    }
    if (includesAny(prompt, ["multi-stage", "platform", "compiler", "distributed", "多阶段", "平台", "编译器", "分布式", "大规模"])) {
      complexity = "complex";
      confidence += 5;
    }
    if (rawPrompt.length < 24 && !includesAny(prompt, complexWords)) complexity = "trivial";

    if (includesAny(prompt, highRiskWords)) {
      risk = "high";
      confidence += 8;
    } else if (includesAny(prompt, mediumRiskWords)) {
      risk = "medium";
      confidence += 5;
    }

    if (risk === "high" || complexity === "complex") executionMode = "plan_then_execute";
    else if (taskType === "answer" && complexity === "trivial") executionMode = "direct_answer";
    else if (includesAny(prompt, vagueWords)) executionMode = "ask_clarification";

    let rationale = currentLanguage === "zh" ? "根据任务动作、影响范围和可逆性给出本地演示判定。" : "Estimated locally from task action, scope, and reversibility.";
    if (risk === "high") {
      rationale = currentLanguage === "zh" ? "检测到可能影响生产或不可逆操作，建议先规划并明确验证步骤。" : "Potential production or irreversible impact detected; plan before execution.";
    } else if (taskType === "code_change") {
      rationale = currentLanguage === "zh" ? "检测到代码或文件修改，建议先检查现有实现和约束。" : "Code or file changes detected; inspect existing constraints first.";
    } else if (taskType === "research") {
      rationale = currentLanguage === "zh" ? "检测到调研或对比任务，建议先限定来源和评价维度。" : "Research or comparison detected; define sources and criteria first.";
    }

    return {
      task_type: taskType,
      complexity,
      risk,
      execution_mode: executionMode,
      confidence: Math.min(96, confidence),
      rationale,
    };
  }

  function renderAssessment(result) {
    const fields = {
      "result-task-type": result.task_type,
      "result-complexity": result.complexity,
      "result-risk": result.risk,
      "result-mode": result.execution_mode,
      "result-confidence": `${result.confidence}%`,
      "result-rationale": result.rationale,
    };
    Object.entries(fields).forEach(([id, value]) => {
      const element = document.getElementById(id);
      if (element) element.textContent = value;
    });
    const riskElement = document.getElementById("result-risk");
    if (riskElement) {
      riskElement.style.color = result.risk === "high" ? "var(--danger)" : result.risk === "medium" ? "var(--amber)" : "";
    }
    const confidenceFill = document.getElementById("confidence-fill");
    if (confidenceFill) confidenceFill.style.width = `${result.confidence}%`;
  }

  function runDemo() {
    if (!promptInput) return;
    const prompt = promptInput.value.trim();
    if (!prompt) {
      showToast(t("toast.empty"));
      return;
    }
    renderAssessment(classifyPrompt(prompt));
  }

  if (runButton) runButton.addEventListener("click", runDemo);

  document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const sample = target.closest("[data-demo-prompt-en]");
    if (!(sample instanceof HTMLElement) || !promptInput) return;
    promptInput.value = currentLanguage === "zh" ? sample.dataset.demoPromptZh || "" : sample.dataset.demoPromptEn || "";
    document.getElementById("demo")?.scrollIntoView({ behavior: "smooth", block: "start" });
    window.setTimeout(runDemo, 280);
  });

  const revealElements = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealElements.forEach((element) => observer.observe(element));
  } else {
    revealElements.forEach((element) => element.classList.add("visible"));
  }

  updateDemoPromptForLanguage();
  applyLanguage(getStoredLanguage() || currentLanguage);
})();
