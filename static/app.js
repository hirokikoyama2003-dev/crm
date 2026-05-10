// 次回コンタクト日のインライン更新後に確認トースト表示
document.addEventListener('DOMContentLoaded', () => {
  // 期限切れ行のツールチップ初期化
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));
});
