// @omni/auth — frontend auth: session, login, roles, route guards.
export * from './roles';
export { AuthService } from './services/auth.service';
export { authGuard, roleGuard } from './guards/auth.guard';
export { API_URL } from './api-url.token';
export { demoInterceptor } from './demo/demo.interceptor';
export { is_demo_mode, configure_demo_mode } from './demo/demo-mode';

