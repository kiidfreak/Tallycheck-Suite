import { bootstrapApplication } from '@angular/platform-browser';
import { configure_demo_mode } from '@omni/auth';
import { configure_api_base } from '@omni/api-client';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';
import { environment } from './environments/environment';

// Both must run before bootstrap: guards and interceptors read demo mode when
// they are created, and the generated client reads the base URL on every call.
configure_demo_mode(environment.demo, environment.allowDemoOverride);
configure_api_base(environment.apiUrl);

bootstrapApplication(AppComponent, appConfig).catch((err) => console.error(err));
