import { ApplicationConfig, importProvidersFrom, provideZoneChangeDetection } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { LucideAngularModule, icons, TriangleAlert } from 'lucide-angular';
import { provideAuth0, authHttpInterceptorFn } from '@auth0/auth0-angular';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { appRoutes } from './app.routes';
import { environment } from '../environments/environment';
import { API_URL, authInterceptor, demoInterceptor } from '@omni/auth';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(appRoutes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([
      demoInterceptor,
      authInterceptor,
      authHttpInterceptorFn
    ])),
    { provide: API_URL, useValue: environment.apiUrl },
    provideAuth0({
      domain: 'dev-x506paw8afbw6jgu.us.auth0.com',
      clientId: '438nQYs59MzRznaEU0lew3Um4RTSYTKl',
      authorizationParams: {
        redirect_uri: window.location.origin,
        audience: 'https://tallycheck/api',
      },
      cacheLocation: 'localstorage',
      httpInterceptor: {
        allowedList: [
          `${environment.apiUrl}/beacons*`,
          `${environment.apiUrl}/safechild*`,
          `${environment.apiUrl}/employees*`,
          `${environment.apiUrl}/departments*`,
          `${environment.apiUrl}/attendance*`,
          `${environment.apiUrl}/reports*`,
          `${environment.apiUrl}/auth/register*`,
          `${environment.apiUrl}/auth/profile*`,
          `${environment.apiUrl}/auth/users*`
        ]
      }
    }),
    importProvidersFrom(LucideAngularModule.pick({ ...icons, AlertTriangle: TriangleAlert })),
  ],
};
