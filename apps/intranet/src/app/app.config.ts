import { ApplicationConfig, importProvidersFrom, provideZoneChangeDetection } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { LucideAngularModule, icons } from 'lucide-angular';
import { provideAuth0, authHttpInterceptorFn } from '@auth0/auth0-angular';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { appRoutes } from './app.routes';
import { environment } from '../environments/environment';
import { API_URL, authInterceptor } from '@omni/auth';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(appRoutes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([
      authInterceptor,
      authHttpInterceptorFn
    ])),
    { provide: API_URL, useValue: environment.apiUrl },
    provideAuth0({
      domain: 'dev-2685h5q7efjt6peh.us.auth0.com',
      clientId: 'GjkjPfZrtR4XAv820vmde7SDlGeUnkwJ',
      authorizationParams: {
        redirect_uri: window.location.origin,
        audience: 'https://intranet/api',
      },
      cacheLocation: 'localstorage',
      httpInterceptor: {
        allowedList: [
          `${environment.apiUrl}/*`
        ]
      }
    }),
    importProvidersFrom(LucideAngularModule.pick(icons)),
  ],
};
