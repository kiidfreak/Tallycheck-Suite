import { InjectionToken } from '@angular/core';

/** Injection token for the backend API base URL. Provided at app level via environment.ts. */
export const API_URL = new InjectionToken<string>('API_URL');
