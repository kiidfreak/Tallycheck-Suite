import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService as Auth0Service } from '@auth0/auth0-angular';
import { AuthService as LocalAuthService } from '../services/auth.service';
import { canAccess } from '../roles';
import { filter, map, switchMap, take } from 'rxjs';
import { toObservable } from '@angular/core/rxjs-interop';

/** Redirect to /login unless a session exists via Auth0. */
export const authGuard: CanActivateFn = () => {
  const auth0 = inject(Auth0Service);
  const router = inject(Router);
  return auth0.isLoading$.pipe(
    filter(loading => !loading),
    take(1),
    switchMap(() => auth0.isAuthenticated$),
    map(isAuth => isAuth ? true : router.createUrlTree(['/login']))
  );
};

/**
 * Per-route role gating.
 */
export const roleGuard: CanActivateFn = (route) => {
  const auth = inject(LocalAuthService);
  const router = inject(Router);
  const id = (route.data?.['id'] as string) ?? '';

  return toObservable(auth.profile_loaded).pipe(
    filter(loaded => loaded === true),
    take(1),
    map(() => {
      if (!id || canAccess(auth.role(), id)) return true;
      return router.createUrlTree(['/home']);
    })
  );
};
