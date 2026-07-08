import { HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { API_URL } from '../api-url.token';
import { map } from 'rxjs';

/**
 * Intercepts outgoing HTTP requests.
 * Prepends API_URL for relative paths and injects Bearer token.
 * Also unwraps uniform backend SuccessResponse wrappers.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const baseUrl = inject(API_URL, { optional: true }) || '';
  const role = auth.role();
  let apiReq = req;

  if (
    req.url.startsWith('/auth') ||
    req.url.startsWith('/attendance') ||
    req.url.startsWith('/employees') ||
    req.url.startsWith('/departments') ||
    req.url.startsWith('/reports')
  ) {
    const isAbsolute = req.url.startsWith('http://') || req.url.startsWith('https://');
    const targetUrl = isAbsolute ? req.url : `${baseUrl}${req.url}`;
    
    apiReq = req.clone({
      url: targetUrl
    });
  }

  return next(apiReq).pipe(
    map(event => {
      if (event instanceof HttpResponse) {
        const body = event.body;
        if (body && typeof body === 'object' && 'message' in body && 'data' in body) {
          if ('meta' in body && body.meta) {
            return event.clone({
              body: {
                data: body.data,
                meta: body.meta,
                records: body.data,
                ...body.meta
              }
            });
          } else {
            return event.clone({ body: body.data });
          }
        }
      }
      return event;
    })
  );
};
