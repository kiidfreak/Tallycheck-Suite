import { ComponentFixture, TestBed } from '@angular/core/testing';
import { LoginComponent } from './login.component';
import { AuthService } from '@omni/auth';
import { Component, Input } from '@angular/core';
import { IconComponent } from '@omni/ui';

@Component({
  // eslint-disable-next-line @angular-eslint/component-selector
  selector: 'omni-icon',
  standalone: true,
  template: '<span>mock icon</span>'
})
class MockIconComponent {
  @Input() name!: string;
}

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  // Create a mock of the AuthService so we don't trigger real Auth0 redirects
  let mockAuthService: { login: jest.Mock };

  beforeEach(async () => {
    mockAuthService = {
      login: jest.fn() // Spy on the login function
    };

    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        { provide: AuthService, useValue: mockAuthService }
      ]
    })
    .overrideComponent(LoginComponent, {
      remove: { imports: [IconComponent] },
      add: { imports: [MockIconComponent] }
    })
    .compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();   });

  it('should create the component successfully', () => {
    expect(component).toBeTruthy();
  });

  it('should correctly set the current year for the footer copyright', () => {
    const currentYear = new Date().getFullYear();
    expect(component.year).toEqual(currentYear);
  });

  it('should call AuthService.login() when submit() is executed', () => {
    component.submit();
    
    // Verify our fake AuthService was triggered exactly once
    expect(mockAuthService.login).toHaveBeenCalledTimes(1);
  });
});
