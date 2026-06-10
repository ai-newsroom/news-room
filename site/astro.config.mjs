import { defineConfig } from 'astro/config';

// GitHub Pages 프로젝트 사이트 기준.
// site는 GitHub 사용자명에 맞게 수정할 것.
export default defineConfig({
  site: 'https://OWNER.github.io',
  base: '/news-room',
});
