(() => {
  "use strict";

  const header = document.querySelector(".site-header");
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector(".nav-links");
  const promptInput = document.getElementById("demo-prompt");
  const runButton = document.getElementById("run-demo");
  const toast = document.getElementById("copy-toast");

  function setHeaderState() {
    if (header) header.classList.toggle("scrolled", window.scrollY > 12);
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

  let toastTimer = 0;
  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 1800);
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
      showToast("已复制到剪贴板");
    } catch {
      showToast("复制失败，请手动选择");
    }
  });

  function includesAny(text, words) {
    return words.some((word) => text.includes(word));
  }

  function classifyPrompt(rawPrompt) {
    const prompt = rawPrompt.trim().toLowerCase();
    const isChinese = /[\u3400-\u9fff]/.test(prompt);
    let taskType = "other";
    let complexity = "simple";
    let risk = "low";
    let executionMode = "inspect_then_act";
    let confidence = 62;

    if (includesAny(prompt, ["code", "bug", "refactor", "test", "实现", "代码", "重构", "修复", "测试", "功能"])) {
      taskType = "code_change";
      confidence += 7;
    } else if (includesAny(prompt, ["research", "compare", "调研", "对比", "分析", "搜索", "资料"])) {
      taskType = "research";
      confidence += 8;
    } else if (includesAny(prompt, ["browser", "website", "网页", "浏览器", "点击", "填写表单"])) {
      taskType = "browser_automation";
      confidence += 6;
    } else if (includesAny(prompt, ["plan", "architecture", "strategy", "方案", "架构", "规划", "路线图"])) {
      taskType = "planning";
      confidence += 7;
    } else if (includesAny(prompt, ["explain", "what is", "解释", "是什么", "回答", "说明"])) {
      taskType = "answer";
      confidence += 4;
    } else if (includesAny(prompt, ["brainstorm", "discuss", "讨论", "头脑风暴", "聊聊"])) {
      taskType = "conversation";
      confidence += 3;
    }

    const complexWords = ["architecture", "migration", "migrate", "cross-file", "multiple", "production", "database", "security", "架构", "迁移", "跨文件", "多个文件", "数据库", "安全", "生产", "并发"];
    if (includesAny(prompt, complexWords) || rawPrompt.length > 90) {
      complexity = "moderate";
      confidence += 6;
    }
    if (includesAny(prompt, ["multi-stage", "platform", "compiler", "distributed", "多阶段", "平台", "编译器", "分布式", "大规模"])) {
      complexity = "complex";
      confidence += 5;
    }
    if (rawPrompt.length < 24 && !includesAny(prompt, complexWords)) complexity = "trivial";

    if (includesAny(prompt, ["production", "deploy", "deployment", "delete", "drop table", "credential", "payment", "生产", "部署", "删除", "数据库表", "凭据", "密钥", "支付"])) {
      risk = "high";
      confidence += 8;
    } else if (includesAny(prompt, ["write", "modify", "refactor", "migrate", "commit", "push", "修改", "写入", "重构", "迁移", "提交", "推送"])) {
      risk = "medium";
      confidence += 5;
    }

    if (risk === "high" || complexity === "complex") executionMode = "plan_then_execute";
    else if (taskType === "answer" && complexity === "trivial") executionMode = "direct_answer";
    else if (includesAny(prompt, ["not sure", "ambiguous", "不清楚", "不确定", "需要确认"])) executionMode = "ask_clarification";

    let rationale = isChinese ? "根据任务动作、影响范围和可逆性给出本地演示判定。" : "Estimated locally from task action, scope, and reversibility.";
    if (risk === "high") rationale = isChinese ? "检测到可能影响生产或不可逆操作，建议先规划并明确验证步骤。" : "Potential production or irreversible impact detected; plan before execution.";
    else if (taskType === "code_change") rationale = isChinese ? "检测到代码或文件修改，建议先检查现有实现和约束。" : "Code or file changes detected; inspect existing constraints first.";
    else if (taskType === "research") rationale = isChinese ? "检测到调研或对比任务，建议先限定来源和评价维度。" : "Research or comparison detected; define sources and criteria first.";

    return { task_type: taskType, complexity, risk, execution_mode: executionMode, confidence: Math.min(96, confidence), rationale };
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
    if (riskElement) riskElement.style.color = result.risk === "high" ? "var(--danger)" : "";
    const confidenceFill = document.getElementById("confidence-fill");
    if (confidenceFill) confidenceFill.style.width = `${result.confidence}%`;
  }

  function runDemo() {
    if (!promptInput) return;
    const prompt = promptInput.value.trim();
    if (!prompt) {
      showToast("请先输入一个任务");
      promptInput.focus();
      return;
    }
    renderAssessment(classifyPrompt(prompt));
  }

  if (runButton) runButton.addEventListener("click", runDemo);

  document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const sample = target.closest("[data-demo-prompt]");
    if (!(sample instanceof HTMLElement) || !promptInput) return;
    promptInput.value = sample.dataset.demoPrompt || "";
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

  if (promptInput) runDemo();
})();
