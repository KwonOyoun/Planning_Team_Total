// Global utility functions
document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(el => {
        const tooltipText = el.getAttribute('data-tooltip');
        el.addEventListener('mouseenter', () => {
            const tooltip = document.createElement('div');
            tooltip.className = 'absolute z-50 bg-gray-900 text-white px-3 py-1 rounded text-sm whitespace-nowrap';
            tooltip.textContent = tooltipText;
            document.body.appendChild(tooltip);
            
            const rect = el.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
            tooltip.style.left = `${rect.left + rect.width/2 - tooltip.offsetWidth/2}px`;
            
            el._tooltip = tooltip;
        });
        
        el.addEventListener('mouseleave', () => {
            if (el._tooltip) {
                el._tooltip.remove();
                delete el._tooltip;
            }
        });
    });
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

document.addEventListener('DOMContentLoaded', () => {
  const intro = document.getElementById('intro-video');
  const video = document.getElementById('introPlayer');

  if (!intro || !video) return;

  let skipped = false;

  const skipIntro = () => {
    if (skipped) return;
    skipped = true;

    // 🎬 영상 안전하게 멈추기
    try {
      video.pause();
    } catch (e) {}

    // 페이드 아웃
    intro.classList.add('fade-out');

    // ⏱️ transition 후 제거 (구형 브라우저 대응)
    setTimeout(() => {
      if (intro.parentNode) {
        intro.parentNode.removeChild(intro);
      }
    }, 1000);
  };

  // ⏱️ 3.8초 후 자동 종료
  setTimeout(skipIntro, 3800);

  // 🎬 영상 끝나면 종료
  video.addEventListener('ended', skipIntro);

  // 🖱️ 클릭하면 즉시 스킵
  intro.addEventListener('click', skipIntro);
});

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.dev-disabled').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      alert('현재 개발 중인 기능입니다.');
    });
  });
});
